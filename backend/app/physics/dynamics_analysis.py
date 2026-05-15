"""Uproszczona analiza: przewrócenie zestawu, luz przy prędkościach, upchnięcie pod sufit."""

from __future__ import annotations

from app.models.schemas import (
    LoadSafetyAnalysis,
    LoadingPlan,
    PackagingRiskItem,
    PlacedBox,
    Product,
    RolloverEstimate,
    SpeedScenarioRisk,
    Trailer,
)
from app.services.recommendations import build_recommendations

G = 9.81


def _product_map(products: list[Product]) -> dict[str, Product]:
    return {p.product_id: p for p in products}


def _effective_packaging(p: Product) -> tuple[str, float, float, float]:
    kind = p.packaging_kind
    if kind == "rigid" and p.compressible:
        kind = "compressible"
    void = p.internal_void_ratio
    if kind == "max_packed" and void < 0.05:
        void = 0.12
    if kind == "compressible" and void < 0.08:
        void = 0.2
    friction = 0.55
    if p.physics and p.physics.friction is not None:
        friction = p.physics.friction
    elif kind in ("compressible", "max_packed"):
        friction = 0.38
    return kind, void, p.max_compress_mm, friction


def _com_mm(boxes: list[PlacedBox]) -> tuple[float, float, float] | None:
    if not boxes:
        return None
    wx = wy = wz = wsum = 0.0
    for b in boxes:
        m = max(b.weight_kg, 1e-6)
        wx += (b.x_mm + b.length_mm / 2) * m
        wy += (b.y_mm + b.width_mm / 2) * m
        wz += (b.z_mm + b.height_mm / 2) * m
        wsum += m
    if wsum < 1e-9:
        return None
    return wx / wsum, wy / wsum, wz / wsum


def _rollover(trailer: Trailer, com_z_mm: float) -> RolloverEstimate:
    deck_m = trailer.deck_height_mm / 1000.0
    load_com_m = com_z_mm / 1000.0
    h_total = deck_m + load_com_m
    half_track = max(trailer.track_width_mm / 2000.0, 0.5)
    static_g = half_track / h_total if h_total > 0.05 else 99.0
    design_g = trailer.max_lateral_accel_g
    util = design_g / static_g if static_g > 0.01 else 9.9
    ok = util <= 0.72
    if ok:
        summary = f"Zapas stateczności poprzecznej OK (wykorzystanie {util * 100:.0f}% marginesu)."
    elif util <= 0.9:
        summary = f"Podwyższone ryzyko przechyłu przy skręcie ({util * 100:.0f}% marginesu)."
    else:
        summary = f"Wysokie ryzyko przewrócenia zestawu ({util * 100:.0f}% — obniż CM lub zwolnij)."
    return RolloverEstimate(
        com_height_road_m=round(h_total, 2),
        static_rollover_lateral_g=round(static_g, 2),
        design_lateral_g=design_g,
        utilization_ratio=round(util, 3),
        ok=ok,
        summary=summary,
    )


def _speed_lateral_g(trailer: Trailer, speed_kmh: int) -> float:
    base = trailer.max_lateral_accel_g
    if speed_kmh <= 50:
        return base * 0.85
    if speed_kmh <= 80:
        return base
    return min(base * 1.12, 0.65)


def _shift_risk(
    box: PlacedBox,
    prod: Product,
    lateral_g: float,
    long_g: float,
) -> PackagingRiskItem | None:
    kind, void, _compress, friction = _effective_packaging(prod)
    if kind == "rigid" and void < 0.05:
        return None
    demand_g = max(lateral_g, long_g * 0.6)
    capacity_g = friction * (1.0 - void)
    margin = capacity_g - demand_g
    if kind == "max_packed":
        margin -= 0.08
    if margin >= 0.12:
        return None
    if margin >= 0.0:
        level = "medium"
        reason = (
            f"Opakowanie „{kind}” (pustka ~{void * 100:.0f}%): siła bezwładności ~{demand_g:.2f}g "
            f"blisko granicy tarcia ~{capacity_g:.2f}g — ryzyko przesunięcia luzem."
        )
    else:
        level = "high"
        reason = (
            f"Przy {demand_g:.2f}g poprzecznie tarcie (~{capacity_g:.2f}g efektywne) może nie wystarczyć — "
            f"towar w plastiku / luzem może się przesunąć."
        )
    return PackagingRiskItem(
        instance_id=box.instance_id,
        product_id=box.product_id,
        name=box.name,
        risk_level=level,
        reason=reason,
    )


def _ceiling_ids(trailer: Trailer, boxes: list[PlacedBox], pmap: dict[str, Product]) -> list[str]:
    limit = min(trailer.height_mm, trailer.max_stack_height_mm)
    tol = 40.0
    out: list[str] = []
    for b in boxes:
        top = b.z_mm + b.height_mm
        if top < limit - tol:
            continue
        p = pmap.get(b.product_id)
        if not p:
            continue
        kind, _, compress, _ = _effective_packaging(p)
        if kind in ("compressible", "max_packed") or compress > 0:
            out.append(b.instance_id)
    return out


def analyze_load_safety(
    trailer: Trailer,
    products: list[Product],
    plan: LoadingPlan,
    speeds_kmh: list[int] | None = None,
) -> LoadSafetyAnalysis:
    speeds = speeds_kmh or [50, 80, 90]
    boxes = plan.boxes
    pmap = _product_map(products)
    notes: list[str] = []

    com = _com_mm(boxes)
    if com is None:
        empty = LoadSafetyAnalysis(
            rollover=RolloverEstimate(
                com_height_road_m=trailer.deck_height_mm / 1000,
                static_rollover_lateral_g=0,
                design_lateral_g=trailer.max_lateral_accel_g,
                utilization_ratio=0,
                ok=True,
                summary="Brak ładunku — brak analizy dynamicznej.",
            ),
            speed_scenarios=[],
            packaging_risks=[],
            global_ok=True,
            notes=["Brak skrzynek w planie."],
        )
        return empty.model_copy(update={"recommendations": build_recommendations(trailer, products, plan, empty)})

    rollover = _rollover(trailer, com[2])
    long_g = trailer.max_brake_accel_g

    speed_rows: list[SpeedScenarioRisk] = []
    all_risks: dict[str, PackagingRiskItem] = {}

    for spd in sorted(set(speeds)):
        lat_g = _speed_lateral_g(trailer, spd)
        loose = 0
        unsecured = 0.0
        for b in boxes:
            p = pmap.get(b.product_id)
            if not p:
                continue
            item = _shift_risk(b, p, lat_g, long_g)
            if item:
                loose += 1
                unsecured += b.weight_kg
                prev = all_risks.get(b.instance_id)
                if not prev or (item.risk_level == "high" and prev.risk_level != "high"):
                    all_risks[b.instance_id] = item
        speed_rows.append(
            SpeedScenarioRisk(
                speed_kmh=spd,
                lateral_g=round(lat_g, 2),
                longitudinal_g=long_g,
                loose_units_at_risk=loose,
                unsecured_mass_kg=round(unsecured, 0),
            )
        )

    ceiling = _ceiling_ids(trailer, boxes, pmap)
    if ceiling:
        notes.append(
            f"{len(ceiling)} jednostek przy suficie (max {int(min(trailer.height_mm, trailer.max_stack_height_mm))} mm) — "
            "możliwe upchnięcie plastiku / ściskalne opakowanie."
        )

    packaging_risks = sorted(all_risks.values(), key=lambda r: (0 if r.risk_level == "high" else 1, r.instance_id))

    global_ok = rollover.ok and not any(r.risk_level == "high" for r in packaging_risks)
    if not global_ok and rollover.ok:
        notes.append("Uwaga: wysokie ryzyko przesunięcia ładunku luzem przy założonych przyspieszeniach.")

    analysis = LoadSafetyAnalysis(
        rollover=rollover,
        speed_scenarios=speed_rows,
        packaging_risks=packaging_risks,
        ceiling_packed_ids=ceiling,
        global_ok=global_ok,
        notes=notes,
        recommendations=None,
    )
    recs = build_recommendations(trailer, products, plan, analysis)
    return analysis.model_copy(update={"recommendations": recs})
