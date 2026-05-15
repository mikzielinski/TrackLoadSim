import { useCallback, useEffect, useMemo, useState } from "react";
import type { LoadSafetyAnalysis, LoadingPlan, PlacedBox, Scenario } from "./types/api";
import {
  analyzeLoad,
  exportLoadMapPdf,
  exportPlanJson,
  fetchScenario,
  fetchScenarios,
  importProducts,
  optimizeScenario,
  optimizeWithAi,
  verifyAiConnection,
  withTrailerDefaults,
} from "./services/api";
import { AiOptimizePanel } from "./components/AiOptimizePanel";
import { ProductPanel } from "./components/ProductPanel";
import { TrailerViewport } from "./components/TrailerViewport";
import { LoadInsightsPanel } from "./components/LoadInsightsPanel";
import { RecommendationsPanel } from "./components/RecommendationsPanel";
import { SafetyAnalysisPanel } from "./components/SafetyAnalysisPanel";
import { computeLoadMetrics } from "./utils/loadMetrics";

export default function App() {
  const [list, setList] = useState<{ scenario_id: string; title: string }[]>([]);
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [plan, setPlan] = useState<LoadingPlan | null>(null);
  const [physicsText, setPhysicsText] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [transparent, setTransparent] = useState(true);
  const [exploded, setExploded] = useState(false);
  const [runPhysics, setRunPhysics] = useState(true);
  const [selectedInstanceId, setSelectedInstanceId] = useState<string | null>(null);
  const [safetyAnalysis, setSafetyAnalysis] = useState<LoadSafetyAnalysis | null>(null);
  const [aiStrategy, setAiStrategy] = useState<string | null>(null);

  useEffect(() => {
    fetchScenarios()
      .then(setList)
      .catch((e: Error) => setErr(e.message));
  }, []);

  const loadScenario = useCallback(async (id: string) => {
    setErr(null);
    setBusy(true);
    try {
      const s = await fetchScenario(id);
      setScenario(s);
      setPlan(s.plan);
      setSelectedInstanceId(null);
      setPhysicsText("");
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (list.length && !scenario) void loadScenario(list[0].scenario_id);
  }, [list, scenario, loadScenario]);

  const applyOptimizeResult = (res: Awaited<ReturnType<typeof optimizeScenario>>, modeLabel: string) => {
    setPlan(res.plan);
    setSelectedInstanceId(null);
    const requested = scenario!.products.reduce((s, p) => s + p.quantity, 0);
    const placed = res.plan.boxes.length;
    const ph = res.physics;
    const placeMsg =
      placed < requested ? `Ułożono ${placed} / ${requested} szt.` : `Ułożono ${placed} szt. (${modeLabel}).`;
    const warnMsg = res.plan.warnings.length ? ` Ostrzeżenia: ${res.plan.warnings.join(" ")}` : "";
    const phLabel = ph.mode === "pybullet" ? "PyBullet" : ph.mode === "skipped" ? "bez symulacji" : ph.mode;
    setPhysicsText(`${placeMsg}${warnMsg} · [${phLabel}] ${ph.message}${ph.steps_simulated ? ` · kroki: ${ph.steps_simulated}` : ""}`);
  };

  const onOptimize = async () => {
    if (!scenario) return;
    setBusy(true);
    setErr(null);
    try {
      const res = await optimizeScenario(scenario, runPhysics, "greedy");
      applyOptimizeResult(res, "układ podstawowy");
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const onOptimizeAi = async (userNotes: string, apiKey: string | null) => {
    if (!scenario) return;
    setBusy(true);
    setErr(null);
    try {
      const res = await optimizeWithAi(scenario, runPhysics, userNotes, apiKey, plan);
      setAiStrategy(res.guidance.strategy_summary);
      if (res.safety_analysis) setSafetyAnalysis(res.safety_analysis);
      applyOptimizeResult(res, `AI · ${res.guidance.pack_mode}`);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const onOptimizeStacked = async () => {
    if (!scenario) return;
    setBusy(true);
    setErr(null);
    try {
      const res = await optimizeScenario(scenario, runPhysics, "stacked");
      applyOptimizeResult(res, "stosy pionowe");
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const onImport: React.ChangeEventHandler<HTMLInputElement> = async (e) => {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (!f) return;
    setBusy(true);
    setErr(null);
    try {
      const s = await importProducts(f);
      setScenario(s);
      setPlan(s.plan);
      setPhysicsText("Import: nowy plan z backendu.");
      setList((prev) => (prev.some((x) => x.scenario_id === s.scenario_id) ? prev : [...prev, { scenario_id: s.scenario_id, title: s.title }]));
    } catch (ex) {
      setErr((ex as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const displayPlan: LoadingPlan | null = useMemo(() => {
    if (!scenario) return null;
    return (
      plan ??
      ({
        boxes: [],
        total_weight_kg: 0,
        utilization_volume: 0,
        warnings: ["Brak planu — użyj „Przelicz rozmieszczenie”."],
      } as LoadingPlan)
    );
  }, [scenario, plan]);

  useEffect(() => {
    if (!selectedInstanceId || !displayPlan) return;
    if (!displayPlan.boxes.some((b) => b.instance_id === selectedInstanceId)) {
      setSelectedInstanceId(null);
    }
  }, [displayPlan, selectedInstanceId]);

  const loadMetrics = useMemo(() => {
    if (!scenario || !displayPlan) return null;
    return computeLoadMetrics(withTrailerDefaults(scenario.trailer), displayPlan, scenario.products);
  }, [scenario, displayPlan]);

  useEffect(() => {
    if (!scenario || !displayPlan?.boxes.length) {
      setSafetyAnalysis(null);
      return;
    }
    let cancelled = false;
    void analyzeLoad(scenario.trailer, scenario.products, displayPlan)
      .then((a) => {
        if (!cancelled) setSafetyAnalysis(a);
      })
      .catch(() => {
        if (!cancelled) setSafetyAnalysis(null);
      });
    return () => {
      cancelled = true;
    };
  }, [scenario, displayPlan]);

  const onExport = async () => {
    if (!displayPlan) return;
    try {
      const json = await exportPlanJson(displayPlan);
      const blob = new Blob([json], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `loading-plan-${scenario?.scenario_id ?? "export"}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setErr((e as Error).message);
    }
  };

  const onExportPdf = async () => {
    if (!displayPlan || !scenario) return;
    setBusy(true);
    setErr(null);
    try {
      const blob = await exportLoadMapPdf(
        withTrailerDefaults(scenario.trailer),
        displayPlan,
        `Mapa załadunku — ${scenario.title}`,
        scenario.scenario_id,
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `mapa-zaladunku-${scenario.scenario_id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const riskHighlightIds = useMemo(() => {
    if (!safetyAnalysis) return new Set<string>();
    const ids = new Set(safetyAnalysis.packaging_risks.map((r) => r.instance_id));
    for (const id of safetyAnalysis.ceiling_packed_ids) ids.add(id);
    return ids;
  }, [safetyAnalysis]);

  const onFocusBox = useCallback((instanceId: string) => {
    setSelectedInstanceId(instanceId);
  }, []);

  if (!scenario || !displayPlan) {
    return (
      <div className="flex min-h-screen items-center justify-center p-8 text-slate-400">
        {err ? <span className="text-red-400">{err}</span> : busy ? "Ładowanie…" : "Brak scenariusza."}
      </div>
    );
  }

  const selectedBox: PlacedBox | null =
    selectedInstanceId == null ? null : displayPlan.boxes.find((b) => b.instance_id === selectedInstanceId) ?? null;

  const t = withTrailerDefaults(scenario.trailer);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex shrink-0 items-center justify-between border-b border-line bg-panel px-4 py-3">
        <div>
          <h1 className="text-lg font-semibold tracking-tight">TrackLoadSim</h1>
          <p className="text-xs text-slate-500">Planowanie ładunku · widok 3D · FastAPI</p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          {busy && <span className="text-accent">Przetwarzanie…</span>}
          {err && <span className="max-w-md truncate text-red-400">{err}</span>}
        </div>
      </header>
      <main className="grid min-h-0 flex-1 grid-cols-1 gap-3 p-3 lg:grid-cols-[320px_1fr_340px]">
        <ProductPanel products={scenario.products} />
        <div className="relative min-h-[min(70vh,720px)] w-full min-h-0 lg:min-h-0 lg:h-full">
          <TrailerViewport
            trailer={t}
            plan={displayPlan}
            trailerTransparent={transparent}
            exploded={exploded}
            selectedInstanceId={selectedInstanceId}
            riskHighlightIds={riskHighlightIds}
            onSelectBox={(b) => setSelectedInstanceId(b?.instance_id ?? null)}
            centerOfMassMm={loadMetrics!.comMm}
            requestedBoxCount={loadMetrics!.requestedCount}
          />
        </div>
        <aside className="flex min-h-0 flex-col gap-3 overflow-auto rounded-lg border border-line bg-panel2 p-3 text-sm">
          <div>
            <label className="text-xs font-medium uppercase text-slate-500">Scenariusz</label>
            <select
              className="mt-1 w-full rounded border border-line bg-panel px-2 py-2 text-sm"
              value={scenario.scenario_id}
              onChange={(e) => void loadScenario(e.target.value)}
            >
              {list.map((s) => (
                <option key={s.scenario_id} value={s.scenario_id}>
                  {s.title}
                </option>
              ))}
            </select>
            <p className="mt-2 text-xs leading-relaxed text-slate-500">{scenario.description}</p>
          </div>
          <div className="rounded border border-line bg-panel p-3 font-mono text-xs">
            <div className="text-slate-500">Naczepa</div>
            <div className="mt-1 text-slate-200">{t.name}</div>
            <div className="mt-2 space-y-0.5 text-slate-400">
              <div>
                {Math.round(t.length_mm)} × {Math.round(t.width_mm)} × {Math.round(t.height_mm)} mm
              </div>
              <div>Max {t.max_weight_kg.toLocaleString("pl-PL")} kg</div>
              <div>
                Osie: przód {t.axle_load_limits.front_kg} kg · tył {t.axle_load_limits.rear_kg} kg
              </div>
            </div>
          </div>
          <AiOptimizePanel
            busy={busy}
            onVerify={verifyAiConnection}
            onOptimize={(notes, key) => void onOptimizeAi(notes, key)}
            lastStrategy={aiStrategy}
          />
          <RecommendationsPanel report={safetyAnalysis?.recommendations} />
          <LoadInsightsPanel trailer={t} metrics={loadMetrics!} selectedBox={selectedBox} />
          <SafetyAnalysisPanel
            trailer={t}
            analysis={safetyAnalysis}
            selectedInstanceId={selectedInstanceId}
            onFocusBox={onFocusBox}
          />
          {selectedBox && (
            <div className="rounded border border-accent/40 bg-panel p-3 text-xs">
              <div className="flex items-start justify-between gap-2">
                <div className="text-[11px] font-medium uppercase text-slate-500">Wybrana skrzynka</div>
                <button
                  type="button"
                  className="shrink-0 rounded border border-line px-2 py-0.5 text-[11px] text-slate-400 hover:bg-panel2"
                  onClick={() => setSelectedInstanceId(null)}
                >
                  Zamknij
                </button>
              </div>
              <div className="mt-2 font-medium text-slate-100">{selectedBox.name}</div>
              <dl className="mt-2 space-y-1 font-mono text-[11px] text-slate-400">
                <div className="flex justify-between gap-2">
                  <dt className="text-slate-500">Produkt</dt>
                  <dd className="truncate text-slate-300" title={selectedBox.product_id}>
                    {selectedBox.product_id}
                  </dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="text-slate-500">Instancja</dt>
                  <dd className="truncate text-slate-300" title={selectedBox.instance_id}>
                    {selectedBox.instance_id}
                  </dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="text-slate-500">Wymiary (mm)</dt>
                  <dd className="text-slate-300">
                    {Math.round(selectedBox.length_mm)} × {Math.round(selectedBox.width_mm)} × {Math.round(selectedBox.height_mm)}
                  </dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="text-slate-500">Pozycja narożnik (mm)</dt>
                  <dd className="text-right text-slate-300">
                    {Math.round(selectedBox.x_mm)}, {Math.round(selectedBox.y_mm)}, {Math.round(selectedBox.z_mm)}
                  </dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="text-slate-500">Waga</dt>
                  <dd className="text-slate-300">{selectedBox.weight_kg.toLocaleString("pl-PL", { maximumFractionDigits: 1 })} kg</dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="text-slate-500">Kolejność załadunku</dt>
                  <dd className="text-slate-300">{selectedBox.load_order}</dd>
                </div>
                {selectedBox.stacking_group && (
                  <div className="flex justify-between gap-2">
                    <dt className="text-slate-500">Grupa stosowania</dt>
                    <dd className="text-slate-300">{selectedBox.stacking_group}</dd>
                  </div>
                )}
                <div className="flex justify-between gap-2">
                  <dt className="text-slate-500">Kruche</dt>
                  <dd className="text-slate-300">{selectedBox.fragile ? "tak" : "nie"}</dd>
                </div>
                <div className="flex justify-between gap-2">
                  <dt className="text-slate-500">Stabilność</dt>
                  <dd className={selectedBox.unstable ? "text-amber-400" : "text-slate-300"}>
                    {selectedBox.unstable ? "ryzyko (symulacja)" : "OK"}
                  </dd>
                </div>
              </dl>
            </div>
          )}
          {displayPlan.warnings.length > 0 && (
            <div className="rounded border border-amber-900/50 bg-amber-950/30 p-2 text-xs text-amber-200">
              {displayPlan.warnings.map((w: string) => (
                <div key={w}>· {w}</div>
              ))}
            </div>
          )}
          {physicsText && <div className="rounded border border-line bg-panel p-2 font-mono text-[11px] text-slate-400">{physicsText}</div>}
          <div className="space-y-2 border-t border-line pt-3">
            <label className="flex cursor-pointer items-center gap-2 text-xs">
              <input type="checkbox" checked={transparent} onChange={(e) => setTransparent(e.target.checked)} />
              Przezroczysta skrzynia
            </label>
            <label className="flex cursor-pointer items-center gap-2 text-xs">
              <input type="checkbox" checked={exploded} onChange={(e) => setExploded(e.target.checked)} />
              Widok „exploded”
            </label>
            <label className="flex cursor-pointer items-center gap-2 text-xs">
              <input type="checkbox" checked={runPhysics} onChange={(e) => setRunPhysics(e.target.checked)} />
              Walidacja PyBullet po optymalizacji
            </label>
          </div>
          <div className="mt-auto flex flex-col gap-2">
            <p className="text-[11px] leading-snug text-slate-500">
              „Przelicz” buduje plan od zera z kolumny <span className="text-slate-400">szt</span> w tabeli ładunku — ta sama liczba sztuk, inny układ (nie dokleja do bieżącego widoku).
            </p>
            <button
              type="button"
              disabled={busy}
              onClick={() => void onOptimize()}
              className="rounded bg-accent px-3 py-2 text-sm font-medium text-white hover:bg-blue-600 disabled:opacity-50"
            >
              Przelicz rozmieszczenie
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => void onOptimizeStacked()}
              className="rounded border border-emerald-800/60 bg-emerald-950/40 px-3 py-2 text-sm font-medium text-emerald-200 hover:bg-emerald-950/70 disabled:opacity-50"
              title="Układ pionowy: stosy kartonów, cięższe na dole — koryguje rozrzucenie po podłodze"
            >
              Optymalizuj układ (stosy)
            </button>
            <button
              type="button"
              disabled={displayPlan.boxes.length === 0 || busy}
              onClick={() => void onExportPdf()}
              className="rounded border border-line bg-panel px-3 py-2 text-sm hover:bg-panel2 disabled:opacity-50"
            >
              Mapa załadunku (PDF)
            </button>
            <button
              type="button"
              disabled={displayPlan.boxes.length === 0}
              onClick={() => void onExport()}
              className="rounded border border-line bg-panel px-3 py-2 text-sm hover:bg-panel2"
            >
              Eksport JSON
            </button>
            <label className="cursor-pointer rounded border border-dashed border-line bg-panel px-3 py-2 text-center text-sm hover:bg-panel2">
              Import .xlsx / .csv
              <input type="file" accept=".xlsx,.xlsm,.csv" className="hidden" onChange={onImport} />
            </label>
          </div>
        </aside>
      </main>
    </div>
  );
}
