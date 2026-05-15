from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AxleLoadLimits(BaseModel):
    front_kg: float
    rear_kg: float


class Trailer(BaseModel):
    trailer_id: str
    name: str
    length_mm: float
    width_mm: float
    height_mm: float
    max_weight_kg: float
    max_stack_height_mm: float
    axle_load_limits: AxleLoadLimits
    # Parametry do analizy dynamicznej (opcjonalne — mają sensowne domyślne)
    wheelbase_mm: float = Field(default=3800, description="Rozstaw osi jezdnych [mm]")
    track_width_mm: float = Field(default=2040, description="Rozstaw kół / szer. toru jazdy [mm]")
    deck_height_mm: float = Field(default=1180, description="Wys. podłogi ładunkowej nad jezdnią [mm]")
    max_lateral_accel_g: float = Field(default=0.5, description="Projektowe obciążenie poprzeczne (mocowania)")
    max_brake_accel_g: float = Field(default=0.8, description="Hamowanie wzdłuż (mocowania)")


class PhysicsParams(BaseModel):
    mass_kg: float | None = None
    friction: float = 0.65
    restitution: float = 0.1
    compressible: bool | None = None
    max_compression_force_kg: float | None = None


class Product(BaseModel):
    product_id: str
    name: str
    length_mm: float
    width_mm: float
    height_mm: float
    weight_kg: float
    quantity: int = 1
    fragile: bool = False
    compressible: bool = False
    max_stack_weight_kg: float | None = None
    can_rotate: bool = True
    allowed_orientations: list[str] | None = None
    stacking_group: str | None = None
    physics: PhysicsParams | None = None
    packaging_kind: Literal["rigid", "compressible", "max_packed"] = "rigid"
    internal_void_ratio: float = Field(
        default=0.0,
        ge=0.0,
        le=0.85,
        description="Udział pustki wewnątrz opakowania (0=pełne, 0.4=luz)",
    )
    max_compress_mm: float = Field(default=0.0, ge=0.0, description="Maks. ściśnięcie w pionie [mm]")


class PlacedBox(BaseModel):
    instance_id: str
    product_id: str
    name: str
    x_mm: float
    y_mm: float
    z_mm: float
    length_mm: float
    width_mm: float
    height_mm: float
    weight_kg: float
    fragile: bool = False
    stacking_group: str | None = None
    load_order: int
    color: str | None = None
    unstable: bool = False


class LoadingPlan(BaseModel):
    boxes: list[PlacedBox]
    total_weight_kg: float
    utilization_volume: float
    warnings: list[str] = Field(default_factory=list)


class Scenario(BaseModel):
    scenario_id: str
    title: str
    description: str
    trailer: Trailer
    products: list[Product]
    plan: LoadingPlan | None = None


class OptimizeRequest(BaseModel):
    trailer: Trailer
    products: list[Product]
    scenario_id: str | None = None
    run_physics: bool = True


class PhysicsValidationResult(BaseModel):
    ok: bool
    mode: Literal["pybullet", "skipped", "error"]
    message: str
    steps_simulated: int = 0


class OptimizeResponse(BaseModel):
    plan: LoadingPlan
    physics: PhysicsValidationResult


class SpeedScenarioRisk(BaseModel):
    speed_kmh: int
    lateral_g: float
    longitudinal_g: float
    loose_units_at_risk: int
    unsecured_mass_kg: float


class PackagingRiskItem(BaseModel):
    instance_id: str
    product_id: str
    name: str
    risk_level: Literal["low", "medium", "high"]
    reason: str


class RolloverEstimate(BaseModel):
    com_height_road_m: float
    static_rollover_lateral_g: float
    design_lateral_g: float
    utilization_ratio: float
    ok: bool
    summary: str


class LoadSafetyAnalysis(BaseModel):
    rollover: RolloverEstimate
    speed_scenarios: list[SpeedScenarioRisk]
    packaging_risks: list[PackagingRiskItem]
    ceiling_packed_ids: list[str] = Field(default_factory=list)
    global_ok: bool
    notes: list[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    trailer: Trailer
    products: list[Product]
    plan: LoadingPlan
    speeds_kmh: list[int] = Field(default_factory=lambda: [50, 80, 90])
