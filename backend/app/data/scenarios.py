"""Wbudowane scenariusze demonstracyjne — spójne z listą produktów i wymiarami naczepy."""

from __future__ import annotations

from app.models.schemas import (
    AxleLoadLimits,
    LoadingPlan,
    PhysicsParams,
    PlacedBox,
    Product,
    Scenario,
    Trailer,
)

STANDARD_TRAILER = Trailer(
    trailer_id="TRAILER_001",
    name="Naczepa standardowa (plandeka / skrzynia)",
    length_mm=13600,
    width_mm=2450,
    height_mm=2700,
    max_weight_kg=24000,
    max_stack_height_mm=2700,
    axle_load_limits=AxleLoadLimits(front_kg=8000, rear_kg=18000),
    wheelbase_mm=3800,
    track_width_mm=2040,
    deck_height_mm=1180,
    max_lateral_accel_g=0.5,
    max_brake_accel_g=0.8,
)


def _palette(i: int) -> str:
    colors = ["#3b82f6", "#22c55e", "#eab308", "#f97316", "#a855f7", "#ec4899", "#14b8a6"]
    return colors[i % len(colors)]


def _plan_metrics(trailer: Trailer, boxes: list[PlacedBox]) -> tuple[float, float]:
    vol_trailer = trailer.length_mm * trailer.width_mm * trailer.height_mm
    vol_used = sum(b.length_mm * b.width_mm * b.height_mm for b in boxes)
    util = vol_used / vol_trailer if vol_trailer else 0.0
    weight = sum(b.weight_kg for b in boxes)
    return util, weight


def scenario_half_loaded() -> Scenario:
    """
    ~50% powierzchni podłogi (rzut XY), jedna warstwa — „połowa” w sensie decku.

    „Przelicz rozmieszczenie” zawsze buduje plan od zera z sumy quantity (nie zaczyna
    od bieżącego układu); liczba skrzynek po przeliczeniu = suma quantity z listy.
    """
    products = [
        Product(
            product_id="BOX-A",
            name="Karton zbiorczy A",
            length_mm=1200,
            width_mm=800,
            height_mm=900,
            weight_kg=180,
            quantity=13,
            fragile=False,
            compressible=False,
            max_stack_weight_kg=2000,
            can_rotate=True,
            stacking_group="GENERAL",
        ),
        Product(
            product_id="BOX-B",
            name="Karton zbiorczy B",
            length_mm=1000,
            width_mm=1000,
            height_mm=800,
            weight_kg=220,
            quantity=4,
            fragile=False,
            compressible=True,
            max_stack_weight_kg=1500,
            can_rotate=True,
            stacking_group="GENERAL",
        ),
    ]
    pid_map = {p.product_id: p for p in products}
    # A: lewa strona naczepy (brak nakładania w x z blokiem B po prawej). B: x >= 6200 mm.
    positions: list[tuple[float, float, float, str]] = [
        (0, 0, 0, "BOX-A"),
        (1220, 0, 0, "BOX-A"),
        (2440, 0, 0, "BOX-A"),
        (3660, 0, 0, "BOX-A"),
        (4880, 0, 0, "BOX-A"),
        (0, 820, 0, "BOX-A"),
        (1220, 820, 0, "BOX-A"),
        (2440, 820, 0, "BOX-A"),
        (3660, 820, 0, "BOX-A"),
        (4880, 820, 0, "BOX-A"),
        (0, 1640, 0, "BOX-A"),
        (1220, 1640, 0, "BOX-A"),
        (2440, 1640, 0, "BOX-A"),
        (6200, 0, 0, "BOX-B"),
        (7300, 0, 0, "BOX-B"),
        (6200, 1100, 0, "BOX-B"),
        (7300, 1100, 0, "BOX-B"),
    ]
    boxes: list[PlacedBox] = []
    order = 0
    for x, y, z, pid in positions:
        p = pid_map[pid]
        order += 1
        boxes.append(
            PlacedBox(
                instance_id=f"{pid}-{order}",
                product_id=pid,
                name=p.name,
                x_mm=x,
                y_mm=y,
                z_mm=z,
                length_mm=p.length_mm,
                width_mm=p.width_mm,
                height_mm=p.height_mm,
                weight_kg=p.weight_kg,
                fragile=p.fragile,
                stacking_group=p.stacking_group,
                load_order=order,
                color=_palette(order),
            )
        )
    util, weight = _plan_metrics(STANDARD_TRAILER, boxes)
    deck = STANDARD_TRAILER.length_mm * STANDARD_TRAILER.width_mm
    foot = sum(b.length_mm * b.width_mm for b in boxes if b.z_mm < 1.0)
    deck_ratio = foot / deck if deck else 0.0
    plan = LoadingPlan(
        boxes=boxes,
        total_weight_kg=weight,
        utilization_volume=util,
        warnings=[
            f"Powierzchnia podłogi zajęta (rzut XY, z≈0): ok. {deck_ratio * 100:.0f}% skrzyni — nadal niska objętość (dużo wolnej wysokości).",
            "Uwaga: „Przelicz rozmieszczenie” układa od zera wszystkie sztuki z quantity — ta sama liczba co w Ładunku, inny układ i inne ID instancji.",
        ],
    )
    return Scenario(
        scenario_id="S1_HALF_LOADED",
        title="S1 — ok. połowa podłogi (start)",
        description="13×A + 4×B na jednej warstwie; ~50% zajętej powierzchni podłogi naczepy. Po przeliczeniu: ta sama liczba sztuk z listy, nowy rozkład.",
        trailer=STANDARD_TRAILER,
        products=products,
        plan=plan,
    )


def scenario_optimized() -> Scenario:
    """24 moduły EUR (1200×800) w siatce 4×3×2 — quantity = liczba skrzynek w planie."""
    products = [
        Product(
            product_id="PAL-1200",
            name="Moduł 1200×800 (EUR)",
            length_mm=1200,
            width_mm=800,
            height_mm=1000,
            weight_kg=320,
            quantity=24,
            fragile=False,
            compressible=False,
            max_stack_weight_kg=5000,
            can_rotate=True,
            stacking_group="MODULE",
        ),
    ]
    p = products[0]
    cols, rows, layers = 4, 3, 2
    boxes: list[PlacedBox] = []
    order = 0
    for lz in range(layers):
        z = lz * p.height_mm
        for ry in range(rows):
            y = ry * p.width_mm
            for cx in range(cols):
                x = cx * p.length_mm
                if x + p.length_mm > STANDARD_TRAILER.length_mm or y + p.width_mm > STANDARD_TRAILER.width_mm:
                    continue
                if z + p.height_mm > STANDARD_TRAILER.height_mm:
                    continue
                order += 1
                boxes.append(
                    PlacedBox(
                        instance_id=f"PAL-{order}",
                        product_id=p.product_id,
                        name=p.name,
                        x_mm=x,
                        y_mm=y,
                        z_mm=z,
                        length_mm=p.length_mm,
                        width_mm=p.width_mm,
                        height_mm=p.height_mm,
                        weight_kg=p.weight_kg,
                        fragile=p.fragile,
                        stacking_group=p.stacking_group,
                        load_order=order,
                        color=_palette(order),
                    )
                )
    util, weight = _plan_metrics(STANDARD_TRAILER, boxes)
    plan = LoadingPlan(
        boxes=boxes,
        total_weight_kg=weight,
        utilization_volume=util,
        warnings=[],
    )
    return Scenario(
        scenario_id="S2_OPTIMIZED",
        title="S2 — Zwarty układ (2 warstwy)",
        description="Siata 4×3 na podłodze, druga warstwa identycznie — demonstracja wysokiego wykorzystania objętości.",
        trailer=STANDARD_TRAILER,
        products=products,
        plan=plan,
    )


def scenario_overloaded() -> Scenario:
    """Stos 5×3×2 z jednego SKU; górna warstwa z częściową flagą ryzyka."""
    products = [
        Product(
            product_id="COMP-1",
            name="Rolka ściskalna",
            length_mm=800,
            width_mm=800,
            height_mm=600,
            weight_kg=400,
            quantity=30,
            fragile=False,
            compressible=True,
            max_stack_weight_kg=800,
            can_rotate=True,
            stacking_group="ROLLS",
            physics=PhysicsParams(
                friction=0.4,
                restitution=0.05,
                compressible=True,
                max_compression_force_kg=200,
            ),
        ),
    ]
    p = products[0]
    nx, ny, nz = 5, 3, 2
    boxes: list[PlacedBox] = []
    order = 0
    for iz in range(nz):
        z = iz * p.height_mm
        for iy in range(ny):
            y = iy * p.width_mm
            for ix in range(nx):
                x = ix * p.length_mm
                if x + p.length_mm > STANDARD_TRAILER.length_mm or y + p.width_mm > STANDARD_TRAILER.width_mm:
                    continue
                if z + p.height_mm > STANDARD_TRAILER.height_mm:
                    continue
                order += 1
                unstable = iz >= 1 and (ix + iy) % 3 == 0
                boxes.append(
                    PlacedBox(
                        instance_id=f"COMP-{order}",
                        product_id=p.product_id,
                        name=p.name,
                        x_mm=x,
                        y_mm=y,
                        z_mm=z,
                        length_mm=p.length_mm,
                        width_mm=p.width_mm,
                        height_mm=p.height_mm,
                        weight_kg=p.weight_kg,
                        fragile=False,
                        stacking_group=p.stacking_group,
                        load_order=order,
                        color="#f97316" if unstable else "#22c55e",
                        unstable=unstable,
                    )
                )
    util, weight = _plan_metrics(STANDARD_TRAILER, boxes)
    plan = LoadingPlan(
        boxes=boxes,
        total_weight_kg=weight,
        utilization_volume=min(0.985, util),
        warnings=[
            "Wysoki nacisk na dolne warstwy — w praktyce sprawdź limity stosowania i rozkład na osie.",
            "Część górnych skrzynek oznaczona jako wizualne ryzyko (niestabilne) do testów UI.",
        ],
    )
    return Scenario(
        scenario_id="S3_OVERLOAD",
        title="S3 — Gęsty stos / ryzyko",
        description="Regularna siatka 5×3×2 w granicach skrzyni (800 mm w szerokości naczepy mieszczą się 3 rzędy); część góry z flagą unstable.",
        trailer=STANDARD_TRAILER,
        products=products,
        plan=plan,
    )


def scenario_fragile() -> Scenario:
    """Szyby przekładane przekładkami — sensowne wypełnienie szerokości naczepy."""
    products = [
        Product(
            product_id="GLASS",
            name="Szyby (płasko)",
            length_mm=2000,
            width_mm=1200,
            height_mm=50,
            weight_kg=85,
            quantity=6,
            fragile=True,
            compressible=False,
            max_stack_weight_kg=120,
            can_rotate=False,
            allowed_orientations=["FLAT"],
            stacking_group="FRAGILE",
        ),
        Product(
            product_id="FOAM",
            name="Przekładka piankowa",
            length_mm=2000,
            width_mm=1200,
            height_mm=40,
            weight_kg=8,
            quantity=6,
            fragile=False,
            compressible=True,
            max_stack_weight_kg=500,
            can_rotate=False,
            stacking_group="DUNNAGE",
        ),
    ]
    boxes: list[PlacedBox] = []
    order = 0
    for i in range(6):
        z = i * 90
        order += 1
        boxes.append(
            PlacedBox(
                instance_id=f"GLASS-{i + 1}",
                product_id="GLASS",
                name="Szyby (płasko)",
                x_mm=400,
                y_mm=400,
                z_mm=z,
                length_mm=2000,
                width_mm=1200,
                height_mm=50,
                weight_kg=85,
                fragile=True,
                stacking_group="FRAGILE",
                load_order=order,
                color="#38bdf8",
            )
        )
        order += 1
        boxes.append(
            PlacedBox(
                instance_id=f"FOAM-{i + 1}",
                product_id="FOAM",
                name="Przekładka piankowa",
                x_mm=400,
                y_mm=400,
                z_mm=z + 50,
                length_mm=2000,
                width_mm=1200,
                height_mm=40,
                weight_kg=8,
                fragile=False,
                stacking_group="DUNNAGE",
                load_order=order,
                color="#94a3b8",
            )
        )
    util, weight = _plan_metrics(STANDARD_TRAILER, boxes)
    plan = LoadingPlan(
        boxes=boxes,
        total_weight_kg=weight,
        utilization_volume=util,
        warnings=["Ładunek kruchy — w operacji wymuszaj przekładki i limity obciążenia stosu."],
    )
    return Scenario(
        scenario_id="S4_FRAGILE",
        title="S4 — Kruche + dunnage",
        description="Stos szkło / pianka / szkło … niski profil, bez rotacji — test reguł kruchych.",
        trailer=STANDARD_TRAILER,
        products=products,
        plan=plan,
    )


def scenario_mixed() -> Scenario:
    """Baza duża skrzynia + elektronika na wierzchu + 20 małych w siatce (poprawione Y)."""
    products = [
        Product(
            product_id="M1",
            name="Karton M (mały)",
            length_mm=400,
            width_mm=300,
            height_mm=250,
            weight_kg=12,
            quantity=20,
            fragile=False,
            compressible=True,
            max_stack_weight_kg=200,
            can_rotate=True,
            stacking_group="MIX-A",
        ),
        Product(
            product_id="M2",
            name="Karton L",
            length_mm=800,
            width_mm=600,
            height_mm=500,
            weight_kg=45,
            quantity=1,
            fragile=False,
            compressible=False,
            max_stack_weight_kg=800,
            can_rotate=True,
            stacking_group="MIX-B",
        ),
        Product(
            product_id="M3",
            name="Elektronika (krucha)",
            length_mm=600,
            width_mm=400,
            height_mm=200,
            weight_kg=25,
            quantity=1,
            fragile=True,
            compressible=False,
            max_stack_weight_kg=100,
            can_rotate=True,
            stacking_group="ELEC",
        ),
    ]
    boxes: list[PlacedBox] = [
        PlacedBox(
            instance_id="M2-1",
            product_id="M2",
            name="Karton L",
            x_mm=0,
            y_mm=0,
            z_mm=0,
            length_mm=800,
            width_mm=600,
            height_mm=500,
            weight_kg=45,
            fragile=False,
            stacking_group="MIX-B",
            load_order=1,
            color="#22c55e",
        ),
        PlacedBox(
            instance_id="M3-1",
            product_id="M3",
            name="Elektronika (krucha)",
            x_mm=100,
            y_mm=100,
            z_mm=520,
            length_mm=600,
            width_mm=400,
            height_mm=200,
            weight_kg=25,
            fragile=True,
            stacking_group="ELEC",
            load_order=2,
            color="#eab308",
            unstable=True,
        ),
    ]
    order = 2
    cols, rows = 5, 4
    for i in range(20):
        col = i % cols
        row = i // cols
        order += 1
        boxes.append(
            PlacedBox(
                instance_id=f"M1-{i + 1}",
                product_id="M1",
                name="Karton M (mały)",
                x_mm=950 + col * 410,
                y_mm=40 + row * 310,
                z_mm=0,
                length_mm=400,
                width_mm=300,
                height_mm=250,
                weight_kg=12,
                fragile=False,
                stacking_group="MIX-A",
                load_order=order,
                color="#3b82f6",
            )
        )
    util, weight = _plan_metrics(STANDARD_TRAILER, boxes)
    plan = LoadingPlan(
        boxes=boxes,
        total_weight_kg=weight,
        utilization_volume=util,
        warnings=[
            "Mix SKU — krucha elektronika na wierzchu oznaczona jako ryzykowna (test ostrzeżeń).",
        ],
    )
    return Scenario(
        scenario_id="S5_MIXED",
        title="S5 — Mix wymiarów",
        description="Duża skrzynia + strefa małych kartonów w siatce; jedna krucha pozycja na górze L.",
        trailer=STANDARD_TRAILER,
        products=products,
        plan=plan,
    )


def scenario_max_packed() -> Scenario:
    """Palety z towarem upychanym w plastiku (np. pieluchy) — druga warstwa pod sufit."""
    products = [
        Product(
            product_id="DIAPER-PLT",
            name="Paleta pieluchy (plastik, max pack)",
            length_mm=1200,
            width_mm=800,
            height_mm=1750,
            weight_kg=380,
            quantity=10,
            fragile=False,
            compressible=True,
            max_stack_weight_kg=1200,
            can_rotate=False,
            stacking_group="HYGIENE",
            packaging_kind="max_packed",
            internal_void_ratio=0.18,
            max_compress_mm=150,
            physics=PhysicsParams(friction=0.35, compressible=True, max_compression_force_kg=800),
        ),
    ]
    p = products[0]
    boxes: list[PlacedBox] = []
    order = 0
    cols, rows = 4, 2
    ceiling_z = STANDARD_TRAILER.max_stack_height_mm - p.height_mm - 25
    layer_z = [0.0, ceiling_z]
    done = False
    for z in layer_z:
        if done:
            break
        for ry in range(rows):
            if done:
                break
            y = ry * p.width_mm
            for cx in range(cols):
                if order >= p.quantity:
                    done = True
                    break
                x = cx * p.length_mm
                if x + p.length_mm > STANDARD_TRAILER.length_mm or y + p.width_mm > STANDARD_TRAILER.width_mm:
                    continue
                if z + p.height_mm > STANDARD_TRAILER.max_stack_height_mm + 5:
                    continue
                order += 1
                boxes.append(
                    PlacedBox(
                        instance_id=f"DIAPER-{order}",
                        product_id=p.product_id,
                        name=p.name,
                        x_mm=x,
                        y_mm=y,
                        z_mm=z,
                        length_mm=p.length_mm,
                        width_mm=p.width_mm,
                        height_mm=p.height_mm,
                        weight_kg=p.weight_kg,
                        stacking_group=p.stacking_group,
                        load_order=order,
                        color=_palette(order),
                    )
                )
    util, weight = _plan_metrics(STANDARD_TRAILER, boxes)
    top = max((b.z_mm + b.height_mm for b in boxes), default=0)
    plan = LoadingPlan(
        boxes=boxes,
        total_weight_kg=weight,
        utilization_volume=util,
        warnings=[
            f"Warstwa górna blisko sufitu ({top:.0f} mm / {STANDARD_TRAILER.max_stack_height_mm:.0f} mm) — opakowanie ściskalne.",
        ],
    )
    return Scenario(
        scenario_id="S6_MAX_PACKED",
        title="S6 — Max pack (pieluchy / plastik)",
        description="Palety z towarem upychanym w folii, górna warstwa pod sufit — test analizy luzu i przewrócenia.",
        trailer=STANDARD_TRAILER,
        products=products,
        plan=plan,
    )


ALL_SCENARIOS: list[Scenario] = [
    scenario_half_loaded(),
    scenario_optimized(),
    scenario_overloaded(),
    scenario_fragile(),
    scenario_mixed(),
    scenario_max_packed(),
]


def get_scenario(sid: str) -> Scenario | None:
    for s in ALL_SCENARIOS:
        if s.scenario_id == sid:
            return s
    return None
