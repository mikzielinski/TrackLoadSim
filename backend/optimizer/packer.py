from __future__ import annotations

import uuid
from typing import List, Tuple, Optional

import numpy as np

from models.loading_plan import CenterOfGravity, LoadingMetrics, LoadingPlan, PlacedItem
from models.product import Product
from models.trailer import Trailer


ORIENTATION_TRANSFORMS = {
    "UPRIGHT":   lambda l, w, h: (l, w, h),
    "ROTATED_Z": lambda l, w, h: (w, l, h),
    "SIDE_X":    lambda l, w, h: (l, h, w),
    "SIDE_X_Z":  lambda l, w, h: (h, l, w),
    "SIDE_Y":    lambda l, w, h: (h, w, l),
    "SIDE_Y_Z":  lambda l, w, h: (w, h, l),
}

# Maximum (x,y) candidates tracked — trade-off between quality and speed
_MAX_XY_POINTS = 150


class Packer3D:
    """
    3D bin packing using gravity-settling extreme-points with numpy-vectorised collision detection.

    Coordinate convention:
        x = 0  → rear of trailer (loaded first, rear axle)
        x = L  → front / kingpin side
        y = 0  → left wall
        z = 0  → floor

    Axle loads:
        front_load = Σ w_i * x_center_i / L
        rear_load  = total − front_load
    """

    SUPPORT_THRESHOLD = 0.70

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def pack(self, trailer: Trailer, products: List[Product]) -> LoadingPlan:
        items_to_place: List[Product] = []
        for prod in self._sort_products(products):
            for _ in range(prod.quantity):
                items_to_place.append(prod)
        total_count = len(items_to_place)

        # 2-D candidate positions (x, y); z computed via gravity settling at runtime.
        # No domination removal — in 2-D with gravity settling (0,0) would dominate
        # every other point and collapse the set to a single unusable entry.
        xy_set: set = {(0.0, 0.0)}

        placed_items: List[PlacedItem] = []
        # numpy mirror kept in sync for fast vectorised checks
        placed_arr = np.empty((0, 6), dtype=np.float64)  # [x, y, z, l, w, h]
        # per-item metadata parallel to placed_arr rows
        placed_meta: List[dict] = []  # fragile, maxStackWeightKg

        for item in items_to_place:
            best: Optional[Tuple[float, float, float, float, float, float, str]] = None
            best_score = float("-inf")

            for orientation, (l, w, h) in self._get_orientations(item):
                if l > trailer.lengthMm or w > trailer.widthMm or h > trailer.heightMm:
                    continue

                tried: set = set()

                for ep_x, ep_y in xy_set:
                    x = min(ep_x, trailer.lengthMm - l)
                    y = min(ep_y, trailer.widthMm - w)

                    if x < 0 or y < 0:
                        continue
                    if x + l > trailer.lengthMm + 1e-3 or y + w > trailer.widthMm + 1e-3:
                        continue

                    # Gravity-settle: snap z to highest support surface
                    z = self._settle_z(x, y, l, w, placed_arr)

                    if z + h > trailer.heightMm + 1e-3:
                        continue
                    z = min(z, trailer.heightMm - h)
                    if z < 0:
                        continue

                    key = (round(x, 1), round(y, 1), round(z, 1), orientation)
                    if key in tried:
                        continue
                    tried.add(key)

                    if self._has_collision(x, y, z, l, w, h, placed_arr):
                        continue

                    if z > 1e-3 and not self._is_supported(x, y, z, l, w, placed_arr):
                        continue

                    if not self._check_stacking(item, x, y, z, l, w, placed_arr, placed_meta):
                        continue

                    score = self._score(x, y, z, l, w, h, item, trailer)

                    if score > best_score:
                        best_score = score
                        best = (x, y, z, l, w, h, orientation)

            if best is not None:
                x, y, z, l, w, h, orientation = best
                pi = PlacedItem(
                    productId=item.productId,
                    name=item.name,
                    xMm=x, yMm=y, zMm=z,
                    lengthMm=l, widthMm=w, heightMm=h,
                    orientation=orientation,
                    weightKg=item.weightKg,
                    fragile=item.fragile,
                    stackingGroup=item.stackingGroup,
                    maxStackWeightKg=item.maxStackWeightKg,
                )
                placed_items.append(pi)
                placed_arr = np.vstack([placed_arr, [[x, y, z, l, w, h]]])
                placed_meta.append({"fragile": item.fragile, "maxStackWeightKg": item.maxStackWeightKg})
                xy_set = _update_xy_set(xy_set, x, y, l, w, trailer)

        metrics = self._calculate_metrics(placed_items, trailer)
        sequence = self._generate_loading_sequence(placed_items, trailer)

        return LoadingPlan(
            planId=str(uuid.uuid4()),
            trailerId=trailer.trailerId,
            items=placed_items,
            metrics=metrics,
            loadingSequence=sequence,
            totalWeightKg=sum(p.weightKg for p in placed_items),
            placedCount=len(placed_items),
            totalCount=total_count,
        )

    # -------------------------------------------------------------------------
    # Sorting
    # -------------------------------------------------------------------------

    def _sort_products(self, products: List[Product]) -> List[Product]:
        def key(p: Product) -> Tuple:
            vol = p.lengthMm * p.widthMm * p.heightMm
            return (1 if p.fragile else 0, -p.weightKg, -vol, p.loadingPriority)
        return sorted(products, key=key)

    # -------------------------------------------------------------------------
    # Orientations
    # -------------------------------------------------------------------------

    def _get_orientations(self, item: Product) -> List[Tuple[str, Tuple[float, float, float]]]:
        l, w, h = item.lengthMm, item.widthMm, item.heightMm
        if item.allowedOrientations:
            names = item.allowedOrientations
        elif item.canRotate:
            names = list(ORIENTATION_TRANSFORMS.keys())
        else:
            names = ["UPRIGHT"]

        results: List[Tuple[str, Tuple[float, float, float]]] = []
        seen: set = set()
        for name in names:
            if name not in ORIENTATION_TRANSFORMS:
                continue
            dims = ORIENTATION_TRANSFORMS[name](l, w, h)
            k = tuple(sorted(dims))
            if k not in seen:
                seen.add(k)
                results.append((name, dims))
        return results

    # -------------------------------------------------------------------------
    # Vectorised geometry helpers  (operate on placed_arr shape (n,6))
    # -------------------------------------------------------------------------

    def _settle_z(self, x: float, y: float, l: float, w: float,
                  placed_arr: np.ndarray) -> float:
        """Gravity-settle: highest top-z of placed items overlapping footprint (x,y,l,w)."""
        if placed_arr.shape[0] == 0:
            return 0.0
        px, py, pz, pl, pw, ph = placed_arr.T
        ox = np.minimum(x + l, px + pl) - np.maximum(x, px)
        oy = np.minimum(y + w, py + pw) - np.maximum(y, py)
        mask = (ox > 1e-3) & (oy > 1e-3)
        if not np.any(mask):
            return 0.0
        return float(np.max(pz[mask] + ph[mask]))

    def _has_collision(self, x: float, y: float, z: float,
                       l: float, w: float, h: float,
                       placed_arr: np.ndarray) -> bool:
        if placed_arr.shape[0] == 0:
            return False
        px, py, pz, pl, pw, ph = placed_arr.T
        EPS = 1e-3
        no_x = (x >= px + pl - EPS) | (x + l <= px + EPS)
        no_y = (y >= py + pw - EPS) | (y + w <= py + EPS)
        no_z = (z >= pz + ph - EPS) | (z + h <= pz + EPS)
        return bool(np.any(~(no_x | no_y | no_z)))

    def _is_supported(self, x: float, y: float, z: float,
                      l: float, w: float,
                      placed_arr: np.ndarray) -> bool:
        """At least SUPPORT_THRESHOLD of base area supported by items with top at z."""
        if placed_arr.shape[0] == 0:
            return False
        px, py, pz, pl, pw, ph = placed_arr.T
        top_mask = np.abs(pz + ph - z) < 1e-3
        if not np.any(top_mask):
            return False
        ox = np.maximum(0.0, np.minimum(x + l, px[top_mask] + pl[top_mask]) - np.maximum(x, px[top_mask]))
        oy = np.maximum(0.0, np.minimum(y + w, py[top_mask] + pw[top_mask]) - np.maximum(y, py[top_mask]))
        return float(np.sum(ox * oy)) / (l * w) >= self.SUPPORT_THRESHOLD

    # -------------------------------------------------------------------------
    # Stacking constraints  (Python loop — only called when z > 0)
    # -------------------------------------------------------------------------

    def _check_stacking(self, item: Product,
                        x: float, y: float, z: float,
                        l: float, w: float,
                        placed_arr: np.ndarray, placed_meta: List[dict]) -> bool:
        """
        For each item directly below the new item:
          - reject if it is fragile
          - reject if item.weightKg alone exceeds its maxStackWeightKg
            (simplified one-level check; full recursive weight accumulation
             would be O(n²) and is avoided for performance)
        """
        if placed_arr.shape[0] == 0 or z < 1e-3:
            return True

        px, py, pz, pl, pw, ph = placed_arr.T
        top_mask = np.abs(pz + ph - z) < 1e-3
        if not np.any(top_mask):
            return True

        ox = np.minimum(x + l, px[top_mask] + pl[top_mask]) - np.maximum(x, px[top_mask])
        oy = np.minimum(y + w, py[top_mask] + pw[top_mask]) - np.maximum(y, py[top_mask])
        below_indices = np.where(top_mask)[0][(ox > 1e-3) & (oy > 1e-3)]

        for idx in below_indices:
            meta = placed_meta[int(idx)]
            if meta["fragile"]:
                return False
            if item.weightKg > meta["maxStackWeightKg"]:
                return False

        return True

    # -------------------------------------------------------------------------
    # Placement scoring (no O(n) loops — fast formula only)
    # -------------------------------------------------------------------------

    def _score(self, x: float, y: float, z: float,
               l: float, w: float, h: float,
               item: Product, trailer: Trailer) -> float:
        # 1. Prefer rear (x small) — items loaded from rear
        pos_score = -x / trailer.lengthMm

        # 2. Prefer low z (gravity stability)
        height_score = -(z / trailer.heightMm) * 2.0

        # 3. Prefer center width (lateral balance)
        cy = trailer.widthMm / 2.0
        lat_offset = abs((y + w / 2.0) - cy) / cy
        lat_score = -lat_offset * item.weightKg / 100.0

        # 4. Axle balance: heavy items near 45% from rear
        length_pct = (x + l / 2.0) / trailer.lengthMm
        axle_score = -abs(length_pct - 0.45) * item.weightKg / 100.0

        return pos_score + height_score + lat_score + axle_score

    # -------------------------------------------------------------------------
    # Metrics
    # -------------------------------------------------------------------------

    def _calculate_metrics(self, placed_items: List[PlacedItem],
                           trailer: Trailer) -> LoadingMetrics:
        total_vol = trailer.lengthMm * trailer.widthMm * trailer.heightMm
        used_vol = sum(p.lengthMm * p.widthMm * p.heightMm for p in placed_items)
        vol_pct = (used_vol / total_vol * 100.0) if total_vol > 0 else 0.0

        total_w = sum(p.weightKg for p in placed_items)
        wt_pct = (total_w / trailer.maxWeightKg * 100.0) if trailer.maxWeightKg > 0 else 0.0

        # Axle loads (lever principle, x=0 = rear axle)
        if trailer.lengthMm > 0 and total_w > 0:
            front_load = sum(
                p.weightKg * (p.xMm + p.lengthMm / 2.0) / trailer.lengthMm
                for p in placed_items
            )
        else:
            front_load = 0.0
        rear_load = total_w - front_load

        # Centre of gravity
        if total_w > 0:
            cog_x = sum(p.weightKg * (p.xMm + p.lengthMm / 2.0) for p in placed_items) / total_w
            cog_y = sum(p.weightKg * (p.yMm + p.widthMm / 2.0) for p in placed_items) / total_w
            cog_z = sum(p.weightKg * (p.zMm + p.heightMm / 2.0) for p in placed_items) / total_w
        else:
            cog_x = cog_y = cog_z = 0.0

        stability = self._stability_score(placed_items, trailer)

        warnings: List[str] = []
        if front_load > trailer.axleLoadLimits.frontKg:
            warnings.append(
                f"FRONT AXLE OVERLOADED: {front_load:.0f} kg > limit {trailer.axleLoadLimits.frontKg:.0f} kg"
            )
        if rear_load > trailer.axleLoadLimits.rearKg:
            warnings.append(
                f"REAR AXLE OVERLOADED: {rear_load:.0f} kg > limit {trailer.axleLoadLimits.rearKg:.0f} kg"
            )
        if total_w > trailer.maxWeightKg:
            warnings.append(
                f"TOTAL WEIGHT EXCEEDED: {total_w:.0f} kg > limit {trailer.maxWeightKg:.0f} kg"
            )
        cog_pct = (cog_x / trailer.lengthMm * 100.0) if trailer.lengthMm > 0 else 50.0
        if cog_pct < 35.0:
            warnings.append(f"CoG TOO FAR REAR: {cog_pct:.1f}% from rear (ideal 35–65%)")
        elif cog_pct > 65.0:
            warnings.append(f"CoG TOO FAR FRONT: {cog_pct:.1f}% from rear (ideal 35–65%)")
        lat_pct = abs((cog_y - trailer.widthMm / 2.0) / (trailer.widthMm / 2.0)) * 100.0
        if lat_pct > 15.0:
            warnings.append(f"LATERAL IMBALANCE: CoG offset {lat_pct:.1f}% from centreline")

        return LoadingMetrics(
            volumeUtilizationPct=round(vol_pct, 2),
            weightUtilizationPct=round(wt_pct, 2),
            frontAxleLoadKg=round(front_load, 2),
            rearAxleLoadKg=round(rear_load, 2),
            centerOfGravity=CenterOfGravity(
                xMm=round(cog_x, 1),
                yMm=round(cog_y, 1),
                zMm=round(cog_z, 1),
            ),
            stabilityScore=round(stability, 1),
            warnings=warnings,
        )

    def _stability_score(self, placed_items: List[PlacedItem],
                         trailer: Trailer) -> float:
        if not placed_items:
            return 100.0
        total_w = sum(p.weightKg for p in placed_items)
        if total_w == 0:
            return 100.0
        max_h = max(p.zMm + p.heightMm for p in placed_items)
        avg_cog_z = sum(p.weightKg * (p.zMm + p.heightMm / 2.0) for p in placed_items) / total_w
        h_score = max(0.0, 100.0 - (avg_cog_z / max_h) * 50.0) if max_h > 0 else 100.0

        avg_cog_y = sum(p.weightKg * (p.yMm + p.widthMm / 2.0) for p in placed_items) / total_w
        cy = trailer.widthMm / 2.0
        lat_offset = abs(avg_cog_y - cy) / cy if cy > 0 else 0.0
        sym_score = max(0.0, 100.0 - lat_offset * 100.0)

        return h_score * 0.6 + sym_score * 0.4

    # -------------------------------------------------------------------------
    # Loading sequence
    # -------------------------------------------------------------------------

    def _generate_loading_sequence(self, placed_items: List[PlacedItem],
                                   trailer: Trailer) -> List[str]:
        ordered = sorted(placed_items, key=lambda p: (p.xMm, p.zMm, p.yMm))
        seq: List[str] = []
        for i, p in enumerate(ordered, 1):
            xp = (p.xMm + p.lengthMm / 2.0) / trailer.lengthMm
            yp = (p.yMm + p.widthMm / 2.0) / trailer.widthMm
            long_pos = "REAR" if xp < 0.33 else ("MID" if xp < 0.66 else "FRONT")
            lat_pos = "LEFT" if yp < 0.33 else ("CENTER" if yp < 0.66 else "RIGHT")
            floor_lbl = "FLOOR" if p.zMm < 10 else f"LEVEL {int(p.zMm // 500) + 1}"
            orient_note = f" [{p.orientation}]" if p.orientation != "UPRIGHT" else ""
            fragile_note = " ⚠ FRAGILE" if p.fragile else ""
            seq.append(
                f"Step {i}: {p.name}{orient_note} → {long_pos} {lat_pos}, {floor_lbl}"
                f" | x={p.xMm:.0f} y={p.yMm:.0f} z={p.zMm:.0f} mm"
                f" | {p.weightKg:.1f} kg{fragile_note}"
            )
        return seq


# -------------------------------------------------------------------------
# Module-level helpers
# -------------------------------------------------------------------------

def _update_xy_set(xy_set: set, x: float, y: float,
                   l: float, w: float, trailer: Trailer) -> set:
    """
    Add new (x,y) candidates after placing an item.
    No domination removal (see pack() docstring).
    Cap at _MAX_XY_POINTS keeping points closest to packing origin.
    """
    EPS = 1e-3
    xy_set.add((x + l, y))
    xy_set.add((x, y + w))
    xy_set = {
        (px, py) for px, py in xy_set
        if 0 <= px < trailer.lengthMm - EPS and 0 <= py < trailer.widthMm - EPS
    }
    if len(xy_set) > _MAX_XY_POINTS:
        sorted_pts = sorted(xy_set, key=lambda pt: pt[0] + pt[1])
        xy_set = set(sorted_pts[:_MAX_XY_POINTS])
    return xy_set if xy_set else {(0.0, 0.0)}
