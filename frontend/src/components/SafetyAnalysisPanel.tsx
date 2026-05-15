import type { LoadSafetyAnalysis, Trailer } from "../types/api";

function StatusPill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded px-2 py-0.5 font-mono text-[10px] font-semibold ${
        ok ? "bg-emerald-950/80 text-emerald-300" : "bg-red-950/80 text-red-300"
      }`}
    >
      <span aria-hidden>{ok ? "✓" : "✗"}</span>
      {label}
    </span>
  );
}

function riskColor(level: string) {
  if (level === "high") return "text-red-400";
  if (level === "medium") return "text-amber-400";
  return "text-slate-400";
}

export function SafetyAnalysisPanel({
  trailer,
  analysis,
}: {
  trailer: Trailer;
  analysis: LoadSafetyAnalysis | null;
}) {
  if (!analysis) {
    return (
      <div className="rounded border border-line bg-panel p-3 text-xs text-slate-500">
        Analiza dynamiczna — brak planu.
      </div>
    );
  }

  const { rollover } = analysis;
  const wheelbase = trailer.wheelbase_mm ?? 3800;
  const track = trailer.track_width_mm ?? 2040;
  const deck = trailer.deck_height_mm ?? 1180;
  const latG = trailer.max_lateral_accel_g ?? 0.5;
  const brakeG = trailer.max_brake_accel_g ?? 0.8;

  return (
    <div className="space-y-3 rounded border border-line bg-panel p-3 text-xs">
      <div className="flex items-center justify-between gap-2 border-b border-line pb-2">
        <div className="text-[10px] font-medium uppercase text-slate-500">Bezpieczeństwo jazdy (model)</div>
        <StatusPill ok={analysis.global_ok} label={analysis.global_ok ? "OK" : "RYZYKO"} />
      </div>

      <div className="space-y-2 font-mono text-[11px]">
        <div className="text-[10px] uppercase text-slate-500">Parametry naczepy</div>
        <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-slate-400">
          <span>Rozstaw osi</span>
          <span className="text-right text-slate-200">{(wheelbase / 1000).toFixed(2)} m</span>
          <span>Rozstaw kół</span>
          <span className="text-right text-slate-200">{(track / 1000).toFixed(2)} m</span>
          <span>Wys. podłogi</span>
          <span className="text-right text-slate-200">{(deck / 1000).toFixed(2)} m</span>
          <span>Poprzecznie (proj.)</span>
          <span className="text-right text-slate-200">{latG} g</span>
          <span>Hamowanie (proj.)</span>
          <span className="text-right text-slate-200">{brakeG} g</span>
        </div>

        <div className="border-t border-line pt-2">
          <div className="flex items-center justify-between gap-2">
            <span className="text-[10px] uppercase text-slate-500">Ryzyko przewrócenia (uproszczone)</span>
            <StatusPill ok={rollover.ok} label={rollover.ok ? "OK" : "UWAGA"} />
          </div>
          <p className="mt-2 text-[10px] leading-relaxed text-slate-400">{rollover.summary}</p>
          <div className="mt-2 space-y-0.5 text-slate-400">
            <div>
              Śr. ciężkości nad jezdnią: <span className="text-slate-200">{rollover.com_height_road_m.toFixed(2)} m</span>
            </div>
            <div>
              Margines poprzeczny: ~{rollover.static_rollover_lateral_g.toFixed(2)} g (proj. {rollover.design_lateral_g} g →{" "}
              {(rollover.utilization_ratio * 100).toFixed(0)}%)
            </div>
          </div>
        </div>

        <div className="border-t border-line pt-2">
          <div className="text-[10px] uppercase text-slate-500">Prędkość · luz w opakowaniu</div>
          <div className="mt-2 overflow-x-auto">
            <table className="w-full border-collapse text-[10px]">
              <thead className="text-slate-500">
                <tr>
                  <th className="py-1 text-left">km/h</th>
                  <th className="py-1 text-right">g poprz.</th>
                  <th className="py-1 text-right">szt. ryzyko</th>
                  <th className="py-1 text-right">kg</th>
                </tr>
              </thead>
              <tbody>
                {analysis.speed_scenarios.map((row) => (
                  <tr key={row.speed_kmh} className="border-t border-line/60 text-slate-300">
                    <td className="py-1">{row.speed_kmh}</td>
                    <td className="py-1 text-right">{row.lateral_g.toFixed(2)}</td>
                    <td className={`py-1 text-right ${row.loose_units_at_risk > 0 ? "text-amber-400" : ""}`}>
                      {row.loose_units_at_risk}
                    </td>
                    <td className="py-1 text-right">{row.unsecured_mass_kg.toLocaleString("pl-PL", { maximumFractionDigits: 0 })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-[10px] leading-relaxed text-slate-500">
            Luz / max-pack: porównanie siły bezwładności z efektywnym tarciem (pustka w opakowaniu). Nie zastępuje norm mocowania.
          </p>
        </div>

        {analysis.ceiling_packed_ids.length > 0 && (
          <div className="rounded border border-amber-900/40 bg-amber-950/25 p-2 text-[10px] text-amber-200">
            <strong>Upchnięcie pod sufit:</strong> {analysis.ceiling_packed_ids.length} jednostek (
            {analysis.ceiling_packed_ids.slice(0, 4).join(", ")}
            {analysis.ceiling_packed_ids.length > 4 ? "…" : ""}) — plastik może się ściskać, rośnie ryzyko przesunięcia.
          </div>
        )}

        {analysis.packaging_risks.length > 0 && (
          <details className="border-t border-line pt-2" open>
            <summary className="cursor-pointer text-[10px] uppercase text-slate-500">
              Ryzyko przesunięcia ({analysis.packaging_risks.length})
            </summary>
            <ul className="mt-2 max-h-40 space-y-2 overflow-auto">
              {analysis.packaging_risks.map((r) => (
                <li key={r.instance_id} className="rounded border border-line/80 bg-panel2 p-2 text-[10px]">
                  <div className="flex justify-between gap-2">
                    <span className="font-medium text-slate-300">{r.name}</span>
                    <span className={riskColor(r.risk_level)}>{r.risk_level}</span>
                  </div>
                  <div className="mt-0.5 text-slate-500">{r.instance_id}</div>
                  <p className="mt-1 leading-snug text-slate-400">{r.reason}</p>
                </li>
              ))}
            </ul>
          </details>
        )}

        {analysis.notes.map((n) => (
          <p key={n} className="text-[10px] text-slate-500">
            · {n}
          </p>
        ))}
      </div>
    </div>
  );
}
