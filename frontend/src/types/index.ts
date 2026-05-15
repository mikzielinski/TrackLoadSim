// ---------------------------------------------------------------------------
// Trailer types
// ---------------------------------------------------------------------------

export interface AxleLimits {
  frontKg: number;
  rearKg: number;
}

export interface Trailer {
  trailerId: string;
  name: string;
  lengthMm: number;
  widthMm: number;
  heightMm: number;
  maxWeightKg: number;
  maxStackHeightMm: number;
  axleLoadLimits: AxleLimits;
}

// ---------------------------------------------------------------------------
// Product types
// ---------------------------------------------------------------------------

export interface PhysicsProperties {
  friction: number;
  restitution: number;
}

export interface Product {
  productId: string;
  name: string;
  lengthMm: number;
  widthMm: number;
  heightMm: number;
  weightKg: number;
  quantity: number;
  fragile: boolean;
  compressible: boolean;
  maxStackWeightKg: number;
  canRotate: boolean;
  allowedOrientations?: string[];
  stackingGroup: string;
  physics?: PhysicsProperties;
  loadingPriority: number;
}

// ---------------------------------------------------------------------------
// Loading plan types
// ---------------------------------------------------------------------------

export interface PlacedItem {
  productId: string;
  name: string;
  xMm: number;
  yMm: number;
  zMm: number;
  lengthMm: number;
  widthMm: number;
  heightMm: number;
  orientation: string;
  weightKg: number;
  fragile: boolean;
  stackingGroup: string;
}

export interface CenterOfGravity {
  xMm: number;
  yMm: number;
  zMm: number;
}

export interface LoadingMetrics {
  volumeUtilizationPct: number;
  weightUtilizationPct: number;
  frontAxleLoadKg: number;
  rearAxleLoadKg: number;
  centerOfGravity: CenterOfGravity;
  stabilityScore: number;
  warnings: string[];
}

export interface LoadingPlan {
  planId: string;
  trailerId: string;
  items: PlacedItem[];
  metrics: LoadingMetrics;
  loadingSequence: string[];
  totalWeightKg: number;
  placedCount: number;
  totalCount: number;
}

// ---------------------------------------------------------------------------
// Scenario metadata
// ---------------------------------------------------------------------------

export interface ScenarioInfo {
  name: string;
  description: string;
}
