import type { LoadSafetyAnalysis, LoadingPlan, OptimizeResponse, Scenario } from "../types/api";

const TRAILER_DEFAULTS = {
  wheelbase_mm: 3800,
  track_width_mm: 2040,
  deck_height_mm: 1180,
  max_lateral_accel_g: 0.5,
  max_brake_accel_g: 0.8,
} as const;

export function withTrailerDefaults<T extends Scenario["trailer"]>(trailer: T): T {
  return { ...TRAILER_DEFAULTS, ...trailer };
}

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export async function fetchScenarios(): Promise<{ scenario_id: string; title: string }[]> {
  const res = await fetch("/api/scenarios");
  return parseJson(res);
}

export async function fetchScenario(id: string): Promise<Scenario> {
  const res = await fetch(`/api/scenarios/${encodeURIComponent(id)}`);
  return parseJson(res);
}

export async function optimizeScenario(scenario: Scenario, runPhysics: boolean): Promise<OptimizeResponse> {
  const res = await fetch("/api/optimize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      trailer: scenario.trailer,
      products: scenario.products,
      scenario_id: scenario.scenario_id,
      run_physics: runPhysics,
    }),
  });
  return parseJson(res);
}

export async function importProducts(file: File): Promise<Scenario> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch("/api/import/products", {
    method: "POST",
    body: fd,
  });
  return parseJson(res);
}

export async function analyzeLoad(
  trailer: Scenario["trailer"],
  products: Scenario["products"],
  plan: LoadingPlan,
): Promise<LoadSafetyAnalysis> {
  const res = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      trailer: withTrailerDefaults(trailer),
      products,
      plan,
      speeds_kmh: [50, 80, 90],
    }),
  });
  return parseJson(res);
}

export async function exportPlanJson(plan: LoadingPlan): Promise<string> {
  const res = await fetch("/api/export/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(plan),
  });
  const data = await parseJson<{ json: string }>(res);
  return data.json;
}
