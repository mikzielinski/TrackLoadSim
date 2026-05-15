import type { PlacedBox, Trailer } from "../types/api";
import type { LoadMetrics } from "../utils/loadMetrics";
import { inertiaForceHintsKg } from "../utils/loadMetrics";

const MM = 0.001;

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

export function LoadInsightsPanel({
  trailer,
  metrics,
  selectedBox,
}: {
  trailer: Trailer;
  metrics: LoadMetrics;
  selectedBox: PlacedBox | null;
}) {
  const globalOk =
    metrics.weightRatio <= 1.001 && metrics.axleFront.ok && metrics.axleRear.ok;
  const forces = selectedBox ? inertiaForceHintsKg(selectedBox.weight_kg) : null;
  const deckM2 = trailer.length_mm * trailer.width_mm * MM * MM;

  return (
    <div className="space-y-3 rounded border border-line bg-panel p-3 text-xs">
      <div className="flex items-center justify-between gap-2 border-b border-line pb-2">
        <div>
          <div className="text-[10px] font-medium uppercase text-slate-500">Ładunek — podsumowanie</div>
          <div className="mt-0.5 font-mono text-[11px] text-slate-300">
            {(trailer.length_mm / 1000).toFixed(2)} × {(trailer.width_mm / 1000).toFixed(2)} × {(trailer.height_mm / 1000).toFixed(2)} m
            <span className="text-slate-500"> · max </span>
            {trailer.max_weight_kg.toLocaleString("pl-PL")} kg
          </div>
        </div>
        <StatusPill ok={globalOk} label={globalOk ? "OK" : "UWAGA"} />
      </div>

      <div className="space-y-2 font-mono text-[11px]">
        <div className="flex justify-between gap-2">
          <span className="text-slate-500">Skrzynki w planie</span>
          <span className={metrics.countMismatch ? "text-amber-300" : "text-slate-200"}>
            {metrics.boxCount}
            {metrics.requestedCount !== metrics.boxCount && (
              <span className="text-slate-500"> / {metrics.requestedCount} szt. (quantity)</span>
            )}
          </span>
        </div>
        {metrics.countMismatch && (
          <p className="rounded border border-amber-900/40 bg-amber-950/25 px-2 py-1 text-[10px] leading-snug text-amber-200">
            Plan startowy ma inną liczbę sztuk niż suma kolumny „szt”. Użyj „Przelicz rozmieszczenie”, aby zsynchronizować z listą ładunku.
          </p>
        )}

        <div>
          <div className="flex justify-between text-slate-500">
            <span>Masa ładunku</span>
            <span className={metrics.weightRatio > 1 ? "text-red-400" : "text-slate-200"}>
              {metrics.totalWeightKg.toLocaleString("pl-PL", { maximumFractionDigits: 0 })} kg
            </span>
          </div>
          <div className="mt-1 h-1.5 overflow-hidden rounded bg-slate-800">
            <div
              className={`h-full rounded ${metrics.weightRatio > 1 ? "bg-red-500" : "bg-accent"}`}
              style={{ width: `${Math.min(100, metrics.weightRatio * 100)}%` }}
            />
          </div>
        </div>

        <div className="flex justify-between gap-2">
          <span className="text-slate-500">Objętość ładunku</span>
          <span className="text-slate-200">{metrics.volumeUsedM3.toFixed(2)} m³</span>
        </div>
        <div className="flex justify-between gap-2">
          <span className="text-slate-500">Pojemność skrzyni</span>
          <span className="text-slate-400">{metrics.volumeCapacityM3.toFixed(2)} m³</span>
        </div>
        <div className="flex justify-between gap-2">
          <span className="text-slate-500">Wykorzystanie objętości</span>
          <span className="text-slate-200">{(metrics.volumeRatio * 100).toFixed(1)}%</span>
        </div>

        <div className="flex justify-between gap-2">
          <span className="text-slate-500">Warstwy (pionowo)</span>
          <span className={metrics.stackLayers <= 1 ? "text-amber-300" : "text-slate-200"}>
            {metrics.stackLayers}
            <span className="text-slate-500"> · na podłodze {metrics.onFloorCount}/{metrics.boxCount}</span>
          </span>
        </div>

        <div className="border-t border-line pt-2">
          <div className="flex justify-between gap-2">
            <span className="text-slate-500">Powierzchnia podłogi (z≈0)</span>
            <span className="text-slate-200">{(metrics.floorAreaRatio * 100).toFixed(1)}%</span>
          </div>
          <div className="mt-0.5 flex justify-between gap-2 text-[10px] text-slate-500">
            <span>{metrics.floorAreaUsedM2.toFixed(2)} m² zajęte</span>
            <span>{deckM2.toFixed(2)} m² skrzynia</span>
          </div>
        </div>

        <div className="flex justify-between gap-2 border-t border-line pt-2">
          <span className="text-slate-500">LDM (1 = 2,4 m² podłogi)</span>
          <span className="text-slate-200">
            {metrics.ldmOccupied.toFixed(2)} / {metrics.ldmCapacity.toFixed(2)}
          </span>
        </div>

        <div className="border-t border-line pt-2">
          <div className="text-[10px] uppercase text-slate-500">Środek masy (szac.)</div>
          {metrics.comMm && metrics.comFromFrontM != null ? (
            <div className="mt-1 space-y-0.5 text-slate-300">
              <div>
                Od przedniej ściany (x=0): <span className="text-slate-100">{metrics.comFromFrontM.toFixed(2)} m</span>
              </div>
              <div>
                Wzdłuż naczepy: <span className="text-slate-100">{metrics.comAlongLengthPct?.toFixed(1)}%</span> długości
              </div>
              <div className="text-[10px] text-slate-500">
                XYZ środka: {metrics.comMm.x.toFixed(0)} · {metrics.comMm.y.toFixed(0)} · {metrics.comMm.z.toFixed(0)} mm
              </div>
            </div>
          ) : (
            <div className="mt-1 text-slate-500">Brak skrzynek w planie.</div>
          )}
        </div>

        <div className="border-t border-line pt-2">
          <div className="text-[10px] uppercase text-slate-500">Oś — uproszczony model</div>
          <div className="mt-2 flex flex-col gap-2">
            <div className="flex items-center justify-between gap-2">
              <span className="text-slate-400">{metrics.axleFront.label}</span>
              <div className="flex items-center gap-2">
                <span className="text-right text-slate-200">
                  {metrics.axleFront.estimated_kg.toFixed(0)} / {metrics.axleFront.limit_kg.toFixed(0)} kg
                </span>
                <StatusPill ok={metrics.axleFront.ok} label={metrics.axleFront.ok ? "OK" : "ŹLE"} />
              </div>
            </div>
            <div className="flex items-center justify-between gap-2">
              <span className="text-slate-400">{metrics.axleRear.label}</span>
              <div className="flex items-center gap-2">
                <span className="text-right text-slate-200">
                  {metrics.axleRear.estimated_kg.toFixed(0)} / {metrics.axleRear.limit_kg.toFixed(0)} kg
                </span>
                <StatusPill ok={metrics.axleRear.ok} label={metrics.axleRear.ok ? "OK" : "ŹLE"} />
              </div>
            </div>
          </div>
          <p className="mt-2 text-[10px] leading-relaxed text-slate-500">
            Podział masy zależy tylko od położenia środka masy wzdłuż X — nie zastępuje ważenia osi ani homologacji.
          </p>
        </div>

        <details className="border-t border-line pt-2">
          <summary className="cursor-pointer text-[10px] uppercase text-slate-500">Siły bezwładności (orientacyjnie)</summary>
          <p className="mt-2 text-[10px] leading-relaxed text-slate-500">
            Typowe współczynniki do mocowań (EN 12195): hamowanie wzdłuż ~<strong className="text-slate-400">0,8·mg</strong>, przyspieszenie
            w tył ~<strong className="text-slate-400">0,5·mg</strong>, skręt poprzeczny ~<strong className="text-slate-400">0,5·mg</strong> względem masy
            ładunku.
          </p>
          {forces && selectedBox && (
            <div className="mt-2 rounded border border-line bg-panel2 p-2 font-mono text-[10px] text-slate-400">
              <div className="text-slate-300">{selectedBox.name}</div>
              <div className="mt-1">Hamowanie (wzdłuż): ~{forces.forward.toFixed(0)} kg siły</div>
              <div>Skręt / tył: ~{forces.lateral.toFixed(0)} kg</div>
            </div>
          )}
          {!selectedBox && (
            <p className="mt-2 text-[10px] text-slate-600">Kliknij skrzynkę, by zobaczyć wartości dla jej masy.</p>
          )}
        </details>
      </div>
    </div>
  );
}
