import { useCallback, useEffect, useState } from "react";
import type { AiConnectionStatus } from "../types/api";
import { verifyAiConnection } from "../services/api";

const STORAGE_KEY = "trackloadsim_openai_key";

export function AiOptimizePanel({
  busy,
  onVerify,
  onOptimize,
  lastStrategy,
}: {
  busy: boolean;
  onVerify: (apiKey: string | null) => Promise<AiConnectionStatus>;
  onOptimize: (userNotes: string, apiKey: string | null) => void;
  lastStrategy: string | null;
}) {
  const [apiKey, setApiKey] = useState("");
  const [userNotes, setUserNotes] = useState("");
  const [status, setStatus] = useState<AiConnectionStatus | null>(null);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) setApiKey(saved);
  }, []);

  const persistKey = useCallback((key: string) => {
    const trimmed = key.trim();
    if (trimmed) localStorage.setItem(STORAGE_KEY, trimmed);
    else localStorage.removeItem(STORAGE_KEY);
  }, []);

  const handleVerify = async () => {
    setChecking(true);
    try {
      persistKey(apiKey);
      const s = await onVerify(apiKey.trim() || null);
      setStatus(s);
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    void verifyAiConnection(null)
      .then(setStatus)
      .catch(() => {
        setStatus({
          configured: false,
          connected: false,
          model: null,
          message: "Nie można sprawdzić statusu AI.",
        });
      });
  }, []);

  const connected = status?.connected === true;
  const statusColor =
    status == null
      ? "text-slate-500"
      : status.connected
        ? "text-emerald-400"
        : status.configured
          ? "text-amber-400"
          : "text-slate-500";

  return (
    <div className="rounded border border-violet-900/50 bg-violet-950/20 p-3 text-xs">
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium uppercase tracking-wide text-violet-300">Optymalizacja AI (GPT)</span>
        {checking && <span className="text-violet-400">Sprawdzanie…</span>}
      </div>
      <p className="mt-1.5 leading-relaxed text-slate-500">
        Po weryfikacji połączenia model układa ładunek według towaru, ostrzeżeń analizy i Twoich uwag.
      </p>
      {status && <p className={`mt-2 ${statusColor}`}>{status.message}</p>}
      <label className="mt-2 block text-[11px] text-slate-500">
        Klucz OpenAI (opcjonalnie, jeśli brak na serwerze)
        <input
          type="password"
          autoComplete="off"
          className="mt-1 w-full rounded border border-line bg-panel px-2 py-1.5 font-mono text-[11px] text-slate-200"
          placeholder="sk-…"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
        />
      </label>
      <label className="mt-2 block text-[11px] text-slate-500">
        Uwagi do załadunku
        <textarea
          rows={2}
          className="mt-1 w-full resize-y rounded border border-line bg-panel px-2 py-1.5 text-[11px] text-slate-200"
          placeholder="np. kruche z tyłu, palety A razem…"
          value={userNotes}
          onChange={(e) => setUserNotes(e.target.value)}
        />
      </label>
      <div className="mt-2 flex flex-col gap-2">
        <button
          type="button"
          disabled={busy || checking}
          onClick={() => void handleVerify()}
          className="rounded border border-violet-800/60 px-3 py-1.5 text-[11px] text-violet-200 hover:bg-violet-950/50 disabled:opacity-50"
        >
          Zweryfikuj połączenie AI
        </button>
        <button
          type="button"
          disabled={busy || !connected}
          title={connected ? undefined : "Najpierw zweryfikuj połączenie AI"}
          onClick={() => {
            persistKey(apiKey);
            onOptimize(userNotes, apiKey.trim() || null);
          }}
          className="rounded bg-violet-600 px-3 py-2 text-sm font-medium text-white hover:bg-violet-500 disabled:opacity-50"
        >
          Optymalizuj z AI
        </button>
      </div>
      {lastStrategy && (
        <p className="mt-2 rounded border border-line/60 bg-panel/80 p-2 leading-relaxed text-slate-400">
          <span className="text-slate-500">Strategia: </span>
          {lastStrategy}
        </p>
      )}
    </div>
  );
}