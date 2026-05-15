"""Greedy 3D placement with edge-aligned candidate positions."""

from __future__ import annotations

from app.models.schemas import LoadingPlan, PlacedBox, Product, Trailer

Box6 = tuple[float, float, float, float, float, float]


def _overlap(a: Box6, b: Box6) -> bool:
    ax, ay, az, al, aw, ah = a
    bx, by, bz, bl, bw, bh = b
    return not (ax + al <= bx or bx + bl <= ax or ay + aw <= by or by + bw <= ay or az + ah <= bz or bz + bh <= az)


def _footprint_supports(box: Box6, placed: list[Box6]) -> bool:
    x, y, z, l, w, h = box
    if z <= 1.0:
        return True
    foot_area = l * w
    if foot_area < 1e-6:
        return False
    supported = 0.0
    bx2, by2 = x + l, y + w
    for ox, oy, oz, ol, ow, oh in placed:
        if abs((oz + oh) - z) > 5.0:
            continue
        ix0, iy0 = max(x, ox), max(y, oy)
        ix1, iy1 = min(bx2, ox + ol), min(by2, oy + ow)
        if ix1 > ix0 and iy1 > iy0:
            supported += (ix1 - ix0) * (iy1 - iy0)
    return supported >= 0.35 * foot_area


def _orientations(p: Product) -> list[tuple[float, float, float]]:
    nominal = (p.length_mm, p.width_mm, p.height_mm)
    if not p.can_rotate:
        return [nominal]
    if p.allowed_orientations == ["FLAT"]:
        dims = sorted([p.length_mm, p.width_mm, p.height_mm])
        flat = (dims[2], dims[1], dims[0])
        return [flat]
    perms = {
        (p.length_mm, p.width_mm, p.height_mm),
        (p.length_mm, p.height_mm, p.width_mm),
        (p.width_mm, p.length_mm, p.height_mm),
        (p.width_mm, p.height_mm, p.length_mm),
        (p.height_mm, p.length_mm, p.width_mm),
        (p.height_mm, p.width_mm, p.length_mm),
    }
    ordered = [nominal]
    for o in sorted(perms):
        if o not in ordered:
            ordered.append(o)
    return ordered


def _orientation_rank(l: float, w: float, h: float, l_tr: float, w_tr: float) -> tuple[float, float, float]:
    """Lower is better: fit trailer, long side along X, then along Y."""
    if l > l_tr or w > w_tr:
        return (1e9, 1e9, 1e9)
    long_side = max(l, w)
    short_side = min(l, w)
    return (0.0, -long_side, short_side + h * 0.001)


def _placement_score(cand: Box6) -> float:
    """Lower is better: floor first, then front (x), then side (y)."""
    x, y, z, _l, _w, _h = cand
    return z * 1_000_000.0 + x * 10.0 + y


def _axis_candidates(placed: list[Box6], trailer_limit: float, item_dim: float, axis: int) -> list[float]:
    """Start positions aligned to walls and placed box edges on one axis."""
    coords: set[float] = {0.0}
    for box in placed:
        if axis == 0:
            coords.add(box[0])
            coords.add(box[0] + box[3])
        elif axis == 1:
            coords.add(box[1])
            coords.add(box[1] + box[4])
        else:
            coords.add(box[2])
            coords.add(box[2] + box[5])
    return sorted(c for c in coords if c + item_dim <= trailer_limit + 0.5)


def pack_trailer(trailer: Trailer, products: list[Product], grid_mm: float = 50.0) -> LoadingPlan:
    del grid_mm  # kept for API compatibility; candidates are edge-based

    items: list[Product] = []
    max_per_sku = 80
    for p in products:
        q = max(0, min(p.quantity, max_per_sku))
        items.extend([p] * q)

    def item_volume(prod: Product) -> float:
        return prod.length_mm * prod.width_mm * prod.height_mm

    items.sort(key=item_volume, reverse=True)

    placed: list[Box6] = []
    boxes: list[PlacedBox] = []
    warnings: list[str] = []
    order = 0
    l_tr = trailer.length_mm
    w_tr = trailer.width_mm
    h_tr = min(trailer.height_mm, trailer.max_stack_height_mm)

    def try_place(prod: Product) -> PlacedBox | None:
        nonlocal order
        orientations = sorted(
            _orientations(prod),
            key=lambda t: _orientation_rank(t[0], t[1], t[2], l_tr, w_tr),
        )
        best_cand: Box6 | None = None
        best_score = float("inf")
        for length, width, height in orientations:
            if length > l_tr or width > w_tr or height > h_tr:
                continue
            xs = _axis_candidates(placed, l_tr, length, 0)
            ys = _axis_candidates(placed, w_tr, width, 1)
            zs = _axis_candidates(placed, h_tr, height, 2)
            for z in zs:
                for y in ys:
                    for x in xs:
                        cand: Box6 = (x, y, z, length, width, height)
                        if cand[0] + cand[3] > l_tr + 0.5 or cand[1] + cand[4] > w_tr + 0.5 or cand[2] + cand[5] > h_tr + 0.5:
                            continue
                        if any(_overlap(cand, o) for o in placed):
                            continue
                        if not _footprint_supports(cand, placed):
                            continue
                        score = _placement_score(cand)
                        if score < best_score:
                            best_score = score
                            best_cand = cand
        if best_cand is None:
            return None
        order += 1
        pid = prod.product_id
        color = ["#3b82f6", "#22c55e", "#eab308", "#f97316", "#a855f7"][order % 5]
        return PlacedBox(
            instance_id=f"{pid}-o{order}",
            product_id=pid,
            name=prod.name,
            x_mm=best_cand[0],
            y_mm=best_cand[1],
            z_mm=best_cand[2],
            length_mm=best_cand[3],
            width_mm=best_cand[4],
            height_mm=best_cand[5],
            weight_kg=prod.weight_kg,
            fragile=prod.fragile,
            stacking_group=prod.stacking_group,
            load_order=order,
            color=color,
            unstable=False,
        )

    skipped = 0
    for prod in items:
        pb = try_place(prod)
        if pb is None:
            skipped += 1
            continue
        placed.append((pb.x_mm, pb.y_mm, pb.z_mm, pb.length_mm, pb.width_mm, pb.height_mm))
        boxes.append(pb)

    if skipped:
        warnings.append(
            f"Nie udało się ułożyć {skipped} szt. — brak miejsca, wysokości lub reguły podparcia (≥35% powierzchni)."
        )

    tw = sum(b.weight_kg for b in boxes)
    if tw > trailer.max_weight_kg:
        warnings.append("Suma masy przekracza limit naczepy (informacja w MVP).")

    vol_t = l_tr * w_tr * h_tr
    vol_u = sum(b.length_mm * b.width_mm * b.height_mm for b in boxes)
    util = vol_u / vol_t if vol_t else 0.0
    return LoadingPlan(boxes=boxes, total_weight_kg=tw, utilization_volume=util, warnings=warnings)
