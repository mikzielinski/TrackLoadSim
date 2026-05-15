export interface AxleLoadLimits {
  front_kg: number;
  rear_kg: number;
}

export interface Trailer {
  trailer_id: string;
  name: string;
  length_mm: number;
  width_mm: number;
  height_mm: number;
  max_weight_kg: number;
  max_stack_height_mm: number;
  axle_load_limits: AxleLoadLimits;
  wheelbase_mm?: number;
  track_width_mm?: number;
  deck_height_mm?: number;
  max_lateral_accel_g?: number;
  max_brake_accel_g?: number;
}

export interface Product {
  product_id: string;
  name: string;
  length_mm: number;
  width_mm: number;
  height_mm: number;
  weight_kg: number;
  quantity: number;
  fragile: boolean;
  compressible: boolean;
  max_stack_weight_kg: number | null;
  can_rotate: boolean;
  allowed_orientations: string[] | null;
  stacking_group: string | null;
  packaging_kind?: "rigid" | "compressible" | "max_packed";
  internal_void_ratio?: number;
  max_compress_mm?: number;
}

export interface PlacedBox {
  instance_id: string;
  product_id: string;
  name: string;
  x_mm: number;
  y_mm: number;
  z_mm: number;
  length_mm: number;
  width_mm: number;
  height_mm: number;
  weight_kg: number;
  fragile: boolean;
  stacking_group: string | null;
  load_order: number;
  color: string | null;
  unstable: boolean;
}

export interface LoadingPlan {
  boxes: PlacedBox[];
  total_weight_kg: number;
  utilization_volume: number;
  warnings: string[];
}

export interface Scenario {
  scenario_id: string;
  title: string;
  description: string;
  trailer: Trailer;
  products: Product[];
  plan: LoadingPlan | null;
}

export interface PhysicsValidationResult {
  ok: boolean;
  mode: "pybullet" | "skipped" | "error";
  message: string;
  steps_simulated: number;
}

export interface OptimizeResponse {
  plan: LoadingPlan;
  physics: PhysicsValidationResult;
}

export type PackMode = "greedy" | "stacked";

export interface AiConnectionStatus {
  configured: boolean;
  connected: boolean;
  model: string | null;
  message: string;
}

export interface AiPackingGuidance {
  pack_mode: PackMode;
  item_sequence_product_ids: string[];
  fragile_floor_only: boolean;
  strategy_summary: string;
  loading_tips: string[];
  model: string;
}

export interface AiOptimizeResponse {
  plan: LoadingPlan;
  physics: PhysicsValidationResult;
  guidance: AiPackingGuidance;
  connection: AiConnectionStatus;
  safety_analysis?: LoadSafetyAnalysis | null;
}

export interface SpeedScenarioRisk {
  speed_kmh: number;
  lateral_g: number;
  longitudinal_g: number;
  loose_units_at_risk: number;
  unsecured_mass_kg: number;
}

export interface PackagingRiskItem {
  instance_id: string;
  product_id: string;
  name: string;
  risk_level: "low" | "medium" | "high";
  reason: string;
}

export interface RolloverEstimate {
  com_height_road_m: number;
  static_rollover_lateral_g: number;
  design_lateral_g: number;
  utilization_ratio: number;
  ok: boolean;
  summary: string;
}

export type RecommendationStatus = "ok" | "caution" | "critical";

export interface RecommendationSection {
  status: RecommendationStatus;
  headline: string;
  items: string[];
}

export interface SummaryReport {
  status: RecommendationStatus;
  headline: string;
  paragraph: string;
  verdict: string;
  key_metrics: string[];
}

export interface RecommendationsReport {
  loading: RecommendationSection;
  driving: RecommendationSection;
  summary: SummaryReport;
}

export interface LoadSafetyAnalysis {
  rollover: RolloverEstimate;
  speed_scenarios: SpeedScenarioRisk[];
  packaging_risks: PackagingRiskItem[];
  ceiling_packed_ids: string[];
  global_ok: boolean;
  notes: string[];
  recommendations?: RecommendationsReport | null;
}
