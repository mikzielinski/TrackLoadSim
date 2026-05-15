"""
Demo scenarios for the trailer loading optimizer.
Each function returns a dict with 'trailer' (Trailer) and 'products' (List[Product]).
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from models.product import PhysicsProperties, Product
from models.trailer import AxleLimits, Trailer


# ---------------------------------------------------------------------------
# Standard trailer definition helpers
# ---------------------------------------------------------------------------

def _standard_trailer() -> Trailer:
    """13.6m × 2.4m × 2.7m standard curtain-side semi-trailer."""
    return Trailer(
        trailerId="T-STD-001",
        name="Standard Semi-Trailer 13.6m",
        lengthMm=13600.0,
        widthMm=2400.0,
        heightMm=2700.0,
        maxWeightKg=24000.0,
        maxStackHeightMm=2700.0,
        axleLoadLimits=AxleLimits(frontKg=7100.0, rearKg=11500.0),
    )


def _mega_trailer() -> Trailer:
    """Mega-liner 13.6m × 2.48m × 3.0m."""
    return Trailer(
        trailerId="T-MEGA-002",
        name="Mega-Liner 13.6m High Cube",
        lengthMm=13600.0,
        widthMm=2480.0,
        heightMm=3000.0,
        maxWeightKg=26000.0,
        maxStackHeightMm=3000.0,
        axleLoadLimits=AxleLimits(frontKg=7500.0, rearKg=12500.0),
    )


# ---------------------------------------------------------------------------
# Product builder helpers
# ---------------------------------------------------------------------------

def _paper_towels(quantity: int = 1) -> Product:
    return Product(
        productId="P-PT-001",
        name="Paper Towels Box",
        lengthMm=500.0, widthMm=400.0, heightMm=300.0,
        weightKg=12.0, quantity=quantity,
        fragile=False, compressible=True,
        maxStackWeightKg=60.0,
        canRotate=True,
        stackingGroup="paper",
        loadingPriority=7,
    )


def _tv_box(quantity: int = 1) -> Product:
    return Product(
        productId="P-TV-002",
        name="TV Box",
        lengthMm=1200.0, widthMm=700.0, heightMm=800.0,
        weightKg=25.0, quantity=quantity,
        fragile=True, compressible=False,
        maxStackWeightKg=10.0,
        canRotate=False,
        allowedOrientations=["UPRIGHT"],
        stackingGroup="electronics",
        loadingPriority=3,
    )


def _metal_parts(quantity: int = 1) -> Product:
    return Product(
        productId="P-MP-003",
        name="Metal Parts Box",
        lengthMm=400.0, widthMm=300.0, heightMm=200.0,
        weightKg=45.0, quantity=quantity,
        fragile=False, compressible=False,
        maxStackWeightKg=200.0,
        canRotate=True,
        stackingGroup="heavy",
        physics=PhysicsProperties(friction=0.7, restitution=0.05),
        loadingPriority=9,
    )


def _clothing_bundle(quantity: int = 1) -> Product:
    return Product(
        productId="P-CB-004",
        name="Clothing Bundle",
        lengthMm=600.0, widthMm=400.0, heightMm=400.0,
        weightKg=8.0, quantity=quantity,
        fragile=False, compressible=True,
        maxStackWeightKg=40.0,
        canRotate=True,
        stackingGroup="soft",
        loadingPriority=5,
    )


def _tool_set(quantity: int = 1) -> Product:
    return Product(
        productId="P-TS-005",
        name="Tool Set Case",
        lengthMm=800.0, widthMm=500.0, heightMm=300.0,
        weightKg=35.0, quantity=quantity,
        fragile=False, compressible=False,
        maxStackWeightKg=150.0,
        canRotate=True,
        stackingGroup="tools",
        loadingPriority=8,
    )


def _glass_items(quantity: int = 1) -> Product:
    return Product(
        productId="P-GI-006",
        name="Glass Items",
        lengthMm=400.0, widthMm=400.0, heightMm=500.0,
        weightKg=15.0, quantity=quantity,
        fragile=True, compressible=False,
        maxStackWeightKg=0.0,
        canRotate=False,
        allowedOrientations=["UPRIGHT"],
        stackingGroup="fragile",
        physics=PhysicsProperties(friction=0.3, restitution=0.0),
        loadingPriority=1,
    )


def _appliance_box(quantity: int = 1) -> Product:
    return Product(
        productId="P-AB-007",
        name="Home Appliance Box",
        lengthMm=700.0, widthMm=600.0, heightMm=700.0,
        weightKg=30.0, quantity=quantity,
        fragile=False, compressible=False,
        maxStackWeightKg=50.0,
        canRotate=True,
        stackingGroup="electronics",
        loadingPriority=6,
    )


def _furniture_flat(quantity: int = 1) -> Product:
    return Product(
        productId="P-FF-008",
        name="Flat-Pack Furniture",
        lengthMm=1800.0, widthMm=600.0, heightMm=100.0,
        weightKg=20.0, quantity=quantity,
        fragile=False, compressible=False,
        maxStackWeightKg=100.0,
        canRotate=True,
        stackingGroup="furniture",
        loadingPriority=6,
    )


def _drum_barrel(quantity: int = 1) -> Product:
    """Approximated as rectangular cuboid."""
    return Product(
        productId="P-DB-009",
        name="Chemical Drum (200L)",
        lengthMm=600.0, widthMm=600.0, heightMm=900.0,
        weightKg=220.0, quantity=quantity,
        fragile=False, compressible=False,
        maxStackWeightKg=0.0,
        canRotate=False,
        allowedOrientations=["UPRIGHT"],
        stackingGroup="hazmat",
        physics=PhysicsProperties(friction=0.6, restitution=0.05),
        loadingPriority=10,
    )


def _book_box(quantity: int = 1) -> Product:
    return Product(
        productId="P-BB-010",
        name="Books Box",
        lengthMm=400.0, widthMm=300.0, heightMm=300.0,
        weightKg=22.0, quantity=quantity,
        fragile=False, compressible=False,
        maxStackWeightKg=80.0,
        canRotate=True,
        stackingGroup="general",
        loadingPriority=7,
    )


def _ceramic_tiles(quantity: int = 1) -> Product:
    return Product(
        productId="P-CT-011",
        name="Ceramic Tile Crate",
        lengthMm=500.0, widthMm=400.0, heightMm=300.0,
        weightKg=50.0, quantity=quantity,
        fragile=True, compressible=False,
        maxStackWeightKg=80.0,
        canRotate=False,
        allowedOrientations=["UPRIGHT"],
        stackingGroup="fragile",
        loadingPriority=2,
    )


def _bicycle_box(quantity: int = 1) -> Product:
    return Product(
        productId="P-BC-012",
        name="Bicycle Box",
        lengthMm=1600.0, widthMm=300.0, heightMm=900.0,
        weightKg=18.0, quantity=quantity,
        fragile=False, compressible=False,
        maxStackWeightKg=20.0,
        canRotate=True,
        stackingGroup="sports",
        loadingPriority=4,
    )


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

def scenario_half_loaded() -> Dict:
    """
    ~45% volume fill — deliberately under-loaded to show optimization opportunity.
    Mix of light consumer goods loaded inefficiently (small quantities).
    """
    trailer = _standard_trailer()
    products: List[Product] = [
        _paper_towels(quantity=120),
        _clothing_bundle(quantity=80),
        _tool_set(quantity=25),
        _book_box(quantity=60),
        _appliance_box(quantity=10),
    ]
    return {
        "name": "half_loaded",
        "description": "Half-loaded trailer — mixed consumer goods at ~45% fill, showing optimization opportunity",
        "trailer": trailer,
        "products": products,
    }


def scenario_fully_optimized() -> Dict:
    """
    Dense mix targeting ~70%+ volume utilization within weight limits.
    Heavy items placed first (floor-level), light compressibles fill remaining space.
    """
    trailer = _mega_trailer()
    products: List[Product] = [
        _metal_parts(quantity=40),       # 40 × 0.024 m³ = 0.96 m³, 1800 kg
        _tool_set(quantity=35),          # 35 × 0.12 m³  = 4.2 m³,  1225 kg
        _book_box(quantity=200),         # 200 × 0.036 m³ = 7.2 m³, 4400 kg
        _paper_towels(quantity=300),     # 300 × 0.06 m³ = 18.0 m³, 3600 kg
        _clothing_bundle(quantity=150),  # 150 × 0.096 m³ = 14.4 m³, 1200 kg
        _furniture_flat(quantity=12),    # 12 × 0.108 m³ = 1.3 m³,  240 kg
        _appliance_box(quantity=15),     # 15 × 0.294 m³ = 4.4 m³,  450 kg
        _bicycle_box(quantity=4),        # 4 × 0.432 m³  = 1.7 m³,   72 kg
    ]
    return {
        "name": "fully_optimized",
        "description": "Fully optimized load — dense packing at ~70% volume, balanced weight distribution",
        "trailer": trailer,
        "products": products,
    }


def scenario_overloaded() -> Dict:
    """
    Deliberately exceeds total weight and rear-axle limits.
    Heavy drums + metal parts loaded at rear trigger REAR AXLE OVERLOADED warning.
    Total weight ~28 000 kg > trailer limit 24 000 kg.
    """
    trailer = _standard_trailer()
    products: List[Product] = [
        _drum_barrel(quantity=30),       # 30 × 220 kg = 6600 kg, very heavy
        _metal_parts(quantity=80),       # 80 × 45 kg  = 3600 kg
        _ceramic_tiles(quantity=60),     # 60 × 50 kg  = 3000 kg, fragile-heavy
        _book_box(quantity=120),         # 120 × 22 kg = 2640 kg
        _tool_set(quantity=60),          # 60 × 35 kg  = 2100 kg
    ]                                    # Total ~17940 kg but axle limits hit first
    return {
        "name": "overloaded",
        "description": "Overloaded scenario — heavy drums + metal parts exceed axle limits, physics warnings shown",
        "trailer": trailer,
        "products": products,
    }


def scenario_fragile() -> Dict:
    """
    Predominantly fragile goods — glass, ceramics, electronics.
    Fragile items go on floor; only light non-fragile items placed on top.
    Demonstrates strict stacking constraint enforcement.
    """
    trailer = _standard_trailer()
    products: List[Product] = [
        _glass_items(quantity=40),       # fragile, maxStackWeightKg=0 → nothing on top
        _tv_box(quantity=25),            # fragile, maxStackWeightKg=10
        _ceramic_tiles(quantity=50),     # fragile, heavy
        _appliance_box(quantity=30),     # not fragile but heavy, ok as base
        _clothing_bundle(quantity=60),   # light, compressible → can go on top
        _paper_towels(quantity=50),      # light, compressible → can go on top
    ]
    return {
        "name": "fragile",
        "description": "Fragile cargo — glass, TVs, ceramics with strict stacking rules; light goods on top only",
        "trailer": trailer,
        "products": products,
    }


def scenario_mixed_cargo() -> Dict:
    """
    Realistic retail distribution: electronics, clothing, tools, paper, fragile.
    Represents complexity of a real-world mixed B2C delivery run.
    """
    trailer = _standard_trailer()
    products: List[Product] = [
        # Electronics (fragile, must go to floor with clearance)
        _tv_box(quantity=15),
        _appliance_box(quantity=20),
        # Clothing (compressible, can fill odd spaces)
        _clothing_bundle(quantity=100),
        # Tools & hardware
        _tool_set(quantity=30),
        _metal_parts(quantity=40),
        # Paper & books
        _paper_towels(quantity=120),
        _book_box(quantity=80),
        # Fragile specialty
        _glass_items(quantity=20),
        _ceramic_tiles(quantity=25),
        # Sports & furniture (large items, loaded first)
        _bicycle_box(quantity=8),
        _furniture_flat(quantity=10),
    ]
    return {
        "name": "mixed_cargo",
        "description": "Mixed retail cargo — electronics, clothing, tools, paper, fragile goods at ~55% fill",
        "trailer": trailer,
        "products": products,
    }


# Registry for easy lookup by name
SCENARIOS: Dict[str, callable] = {
    "half_loaded": scenario_half_loaded,
    "fully_optimized": scenario_fully_optimized,
    "overloaded": scenario_overloaded,
    "fragile": scenario_fragile,
    "mixed_cargo": scenario_mixed_cargo,
}


def get_scenario(name: str) -> Dict:
    if name not in SCENARIOS:
        raise KeyError(f"Unknown scenario: '{name}'. Available: {list(SCENARIOS.keys())}")
    return SCENARIOS[name]()


def list_scenarios() -> List[Dict]:
    return [
        {
            "name": s["name"],
            "description": s["description"],
        }
        for s in [fn() for fn in SCENARIOS.values()]
    ]
