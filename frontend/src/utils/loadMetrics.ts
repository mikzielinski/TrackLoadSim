import type { LoadingPlan, PlacedBox, Trailer } from "../types/api";

const MM = 0.001;
const LD_M2 = 2.4;

export interface Vec3Mm {
  x: number;
  y: number;
  z: number;
}

export interface AxleEstimate {
  label: string;
  estimated_kg: number;
  limit_kg: number;
  ok: boolean;
}

export interface LoadMetrics {
  boxCount: number;
  requestedCount: number;
  countMismatch: boolean;
  totalWeightKg: number;
  trailerMaxKg: number;
  weightRatio: number;
  volumeUsedM3: number;
  volumeCapacityM3: number;
  volumeRatio: number;
  floorAreaUsedM2: number;
  floorAreaRatio: number;
  ldmOccupied: number;
  ldmCapacity: number;
  comMm: Vec3Mm | null;
  comFromFrontM: number | null;
  comAlongLengthPct: number | null;
  axleFront: AxleEstimate;
  axleRear: AxleEstimate;
  stackLayers: number;
  onFloorCount: number;
}

function boxCenter(b: PlacedBox): Vec3Mm {
  return {
    x: b.x_mm + b.length_mm / 2,
    y: b.y_mm + b.width_mm / 2,
    z: b.z_mm + b.height_mm / 2,
  };
}

function volumeM3(b: PlacedBox): number {
  return b.length_mm * b.width_mm * b.height_mm * MM ** 3;
}

/** Środek masy geometryczny (waga jako masa punktowa w środkach skrzynek). */
export function computeCenterOfMassMm(boxes: PlacedBox[]): Vec3Mm | null {
  if (!boxes.length) return null;
  let wx = 0;
  let wy = 0;
  let wz = 0;
  let wsum = 0;
  for (const b of boxes) {
    const m = Math.max(b.weight_kg, 1e-6);
    const c = boxCenter(b);
    wx += c.x * m;
    wy += c.y * m;
    wz += c.z * m;
    wsum += m;
  }
  if (wsum < 1e-9) return null;
  return { x: wx / wsum, y: wy / wsum, z: wz / wsum };
}

/**
 * Uproszczony podział masy na „przód / tył” naczepy wzdłuż osi X:
 * im dalej środek masy od przedniej ściany (x=0), tym większy udział na tył.
 * Nie uwzględnia rzeczywistego rozstawu osi — tylko wizualny status vs limity w danych.
 */
export function estimateAxleLoadsLinear(
  totalKg: number,
  comXmm: number,
  trailerLengthMm: number,
  _limits: { front_kg: number; rear_kg: number },
): { front_kg: number; rear_kg: number } {
  const L = Math.max(trailerLengthMm, 1);
  const t = Math.min(1, Math.max(0, comXmm / L));
  const rearShare = t;
  const frontShare = 1 - rearShare;
  return {
    front_kg: totalKg * frontShare,
    rear_kg: totalKg * rearShare,
  };
}

export function computeLoadMetrics(
  trailer: Trailer,
  plan: LoadingPlan,
  products?: { quantity: number }[],
): LoadMetrics {
  const boxes = plan.boxes;
  const requestedCount = products?.reduce((s, p) => s + p.quantity, 0) ?? boxes.length;
  const countMismatch = products != null && boxes.length !== requestedCount;
  const L = trailer.length_mm;
  const W = trailer.width_mm;
  const H = Math.min(trailer.height_mm, trailer.max_stack_height_mm);
  const capM3 = L * W * H * MM ** 3;
  const volUsed = boxes.reduce((s, b) => s + volumeM3(b), 0);
  const floorDeckM2 = L * W * MM ** 2;
  const onFloor = boxes.filter((b) => b.z_mm < 5);
  const floorUsedM2 = onFloor.reduce((s, b) => s + b.length_mm * b.width_mm * MM ** 2, 0);
  const zBands = new Set(boxes.map((b) => Math.round(b.z_mm / 40)));
  const stackLayers = zBands.size;
  const totalWeight = boxes.reduce((s, b) => s + b.weight_kg, 0) || plan.total_weight_kg;

  const com = computeCenterOfMassMm(boxes);
  const comFromFrontM = com ? com.x * MM : null;
  const comAlongPct = com && L > 0 ? (com.x / L) * 100 : null;

  const ax = com ? estimateAxleLoadsLinear(totalWeight, com.x, L, trailer.axle_load_limits) : { front_kg: 0, rear_kg: 0 };
  const axleFront: AxleEstimate = {
    label: "Przód (szac.)",
    estimated_kg: ax.front_kg,
    limit_kg: trailer.axle_load_limits.front_kg,
    ok: ax.front_kg <= trailer.axle_load_limits.front_kg * 1.001,
  };
  const axleRear: AxleEstimate = {
    label: "Tył (szac.)",
    estimated_kg: ax.rear_kg,
    limit_kg: trailer.axle_load_limits.rear_kg,
    ok: ax.rear_kg <= trailer.axle_load_limits.rear_kg * 1.001,
  };

  const ldmOcc = floorUsedM2 / LD_M2;
  const ldmCap = floorDeckM2 / LD_M2;

  return {
    boxCount: boxes.length,
    requestedCount,
    countMismatch,
    totalWeightKg: totalWeight,
    trailerMaxKg: trailer.max_weight_kg,
    weightRatio: trailer.max_weight_kg > 0 ? totalWeight / trailer.max_weight_kg : 0,
    volumeUsedM3: volUsed,
    volumeCapacityM3: capM3,
    volumeRatio: capM3 > 0 ? volUsed / capM3 : 0,
    floorAreaUsedM2: floorUsedM2,
    floorAreaRatio: floorDeckM2 > 0 ? floorUsedM2 / floorDeckM2 : 0,
    ldmOccupied: ldmOcc,
    ldmCapacity: ldmCap,
    comMm: com,
    comFromFrontM,
    comAlongLengthPct: comAlongPct,
    axleFront,
    axleRear,
    stackLayers,
    onFloorCount: onFloor.length,
  };
}

/** Siły bezwładności orientacyjne na skrzynkę (tekst do panelu / tooltip). */
export function inertiaForceHintsKg(weightKg: number): { forward: number; lateral: number; rearward: number } {
  return {
    forward: 0.8 * weightKg,
    rearward: 0.5 * weightKg,
    lateral: 0.5 * weightKg,
  };
}
