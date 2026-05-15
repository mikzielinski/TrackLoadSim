import { useMemo, useState } from "react";
import type { Product } from "../types/api";

export function ProductPanel({ products }: { products: Product[] }) {
  const [q, setQ] = useState("");
  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (!s) return products;
    return products.filter(
      (p) =>
        p.name.toLowerCase().includes(s) ||
        p.product_id.toLowerCase().includes(s) ||
        (p.stacking_group && p.stacking_group.toLowerCase().includes(s)),
    );
  }, [products, q]);

  const totalQty = useMemo(() => products.reduce((s, p) => s + p.quantity, 0), [products]);

  return (
    <div className="flex h-full min-h-0 flex-col rounded-lg border border-line bg-panel2">
      <div className="border-b border-line px-3 py-2">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Ładunek</div>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Filtruj nazwę / SKU / grupę…"
          className="mt-2 w-full rounded border border-line bg-panel px-2 py-1.5 text-sm outline-none ring-accent focus:ring-1"
        />
      </div>
      <div className="min-h-0 flex-1 overflow-auto">
        <table className="w-full border-collapse text-left text-xs">
          <thead className="sticky top-0 z-10 bg-panel2 font-mono text-[10px] uppercase text-slate-500">
            <tr>
              <th className="border-b border-line px-2 py-2">SKU</th>
              <th className="border-b border-line px-2 py-2">Nazwa</th>
              <th className="border-b border-line px-2 py-2">L×W×H</th>
              <th className="border-b border-line px-2 py-2">kg</th>
              <th className="border-b border-line px-2 py-2">szt</th>
              <th className="border-b border-line px-2 py-2">opak.</th>
              <th className="border-b border-line px-2 py-2">⚠</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p) => (
              <tr
                key={p.product_id}
                className={`border-b border-line/60 hover:bg-panel ${
                  p.fragile ? "bg-amber-950/20" : ""
                }`}
              >
                <td className="whitespace-nowrap px-2 py-1.5 font-mono text-slate-400">{p.product_id}</td>
                <td className="max-w-[140px] truncate px-2 py-1.5">{p.name}</td>
                <td className="whitespace-nowrap px-2 py-1.5 font-mono text-slate-400">
                  {Math.round(p.length_mm)}×{Math.round(p.width_mm)}×{Math.round(p.height_mm)}
                </td>
                <td className="px-2 py-1.5 font-mono">{p.weight_kg}</td>
                <td className="px-2 py-1.5 font-mono">{p.quantity}</td>
                <td className="px-2 py-1.5 font-mono text-[10px] text-slate-500" title={p.packaging_kind ?? (p.compressible ? "compressible" : "rigid")}>
                  {p.packaging_kind === "max_packed" ? "max" : p.packaging_kind === "compressible" || p.compressible ? "ściśl." : "—"}
                </td>
                <td className="px-2 py-1.5 text-center">
                  {p.fragile ? <span title="Kruszyw">🫧</span> : ""}
                  {p.compressible ? <span title="Ściskalne">📦</span> : ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="border-t border-line px-3 py-2 font-mono text-[11px] text-slate-400">
        Suma kolumny <span className="text-slate-300">szt</span>:{" "}
        <span className="text-slate-200">{totalQty}</span>
        <span className="text-slate-600"> · {products.length} pozycji SKU</span>
      </div>
    </div>
  );
}
