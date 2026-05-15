import React, { useCallback, useEffect, useState } from 'react';
import TrailerScene from './components/TrailerScene';
import ProductList from './components/ProductList';
import MetricsPanel from './components/MetricsPanel';
import ControlPanel from './components/ControlPanel';
import api, { ImportResult } from './services/api';
import { LoadingPlan, ScenarioInfo, Trailer } from './types';

const styles: Record<string, React.CSSProperties> = {
  root: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    background: '#0f172a',
    color: '#e2e8f0',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 20px',
    height: 52,
    background: '#020617',
    borderBottom: '1px solid #1e293b',
    flexShrink: 0,
  },
  headerTitle: {
    fontWeight: 800,
    fontSize: 18,
    color: '#f1f5f9',
    letterSpacing: '-0.02em',
  },
  headerBadge: {
    background: '#1e293b',
    border: '1px solid #334155',
    borderRadius: 6,
    padding: '3px 10px',
    fontSize: 11,
    color: '#94a3b8',
  },
  body: {
    display: 'flex',
    flex: 1,
    overflow: 'hidden',
  },
  leftPanel: {
    width: '22%',
    minWidth: 220,
    maxWidth: 280,
    borderRight: '1px solid #1e293b',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    background: '#080f1e',
  },
  centerPanel: {
    flex: 1,
    overflow: 'hidden',
    position: 'relative',
  },
  rightPanel: {
    width: '24%',
    minWidth: 240,
    maxWidth: 320,
    borderLeft: '1px solid #1e293b',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    background: '#080f1e',
  },
  rightPanelTop: {
    borderBottom: '1px solid #1e293b',
    flexShrink: 0,
  },
  rightPanelBottom: {
    flex: 1,
    overflowY: 'auto',
  },
  toast: {
    position: 'fixed',
    bottom: 20,
    left: '50%',
    transform: 'translateX(-50%)',
    background: '#7f1d1d',
    border: '1px solid #ef4444',
    borderRadius: 8,
    padding: '10px 20px',
    color: '#fca5a5',
    fontSize: 13,
    fontWeight: 600,
    zIndex: 9999,
    maxWidth: 500,
    textAlign: 'center',
  },
  toastSuccess: {
    background: '#064e3b',
    border: '1px solid #10b981',
    color: '#6ee7b7',
  },
};

export default function App(): JSX.Element {
  const [plan, setPlan] = useState<LoadingPlan | null>(null);
  const [scenarios, setScenarios] = useState<ScenarioInfo[]>([]);
  const [trailers, setTrailers] = useState<Trailer[]>([]);
  const [selectedTrailer, setSelectedTrailer] = useState<Trailer | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState<{ message: string; error: boolean } | null>(null);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  const showToast = useCallback(
    (message: string, error = false, duration = 4000): void => {
      setToast({ message, error });
      setTimeout(() => setToast(null), duration);
    },
    [],
  );

  // Bootstrap: load scenarios and trailers
  useEffect(() => {
    const init = async (): Promise<void> => {
      const alive = await api.healthCheck();
      setBackendStatus(alive ? 'online' : 'offline');

      if (!alive) {
        showToast('Backend offline. Start the server at localhost:8000.', true, 8000);
        return;
      }

      try {
        const [fetchedScenarios, fetchedTrailers] = await Promise.all([
          api.getScenarios(),
          api.getTrailers(),
        ]);
        setScenarios(fetchedScenarios);
        setTrailers(fetchedTrailers);
        if (fetchedTrailers.length > 0) {
          setSelectedTrailer(fetchedTrailers[0]);
        }
      } catch {
        showToast('Failed to load scenarios and trailers from backend.', true);
      }
    };

    init();
  }, [showToast]);

  const handleOptimize = useCallback(
    async (scenarioName: string): Promise<void> => {
      setIsLoading(true);
      try {
        const result = await api.optimizeScenario(scenarioName);
        setPlan(result);
        showToast(
          `Optimized: ${result.placedCount}/${result.totalCount} items placed (${result.metrics.volumeUtilizationPct.toFixed(1)}% volume)`,
          false,
        );
        // Sync selected trailer to the one used by the scenario
        const t = trailers.find((tr) => tr.trailerId === result.trailerId);
        if (t) setSelectedTrailer(t);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Optimization failed.';
        showToast(msg, true);
      } finally {
        setIsLoading(false);
      }
    },
    [trailers, showToast],
  );

  const handleImportExcel = useCallback(
    async (file: File): Promise<void> => {
      setIsLoading(true);
      try {
        const result: ImportResult = await api.importExcel(file);
        showToast(
          `Imported ${result.importedCount} products from Excel.${result.errors.length > 0 ? ` ${result.errors.length} row errors.` : ''}`,
          result.errors.length > 0,
        );
      } catch {
        showToast('Excel import failed. Check file format.', true);
      } finally {
        setIsLoading(false);
      }
    },
    [showToast],
  );

  return (
    <div style={styles.root}>
      {/* Header */}
      <header style={styles.header}>
        <span style={styles.headerTitle}>AI Trailer Loading Optimizer</span>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {plan && (
            <span style={{ fontSize: 12, color: '#94a3b8' }}>
              {plan.placedCount} items &bull; {plan.metrics.volumeUtilizationPct.toFixed(1)}% vol &bull;{' '}
              {plan.totalWeightKg.toFixed(0)} kg
            </span>
          )}
          <span
            style={{
              ...styles.headerBadge,
              borderColor:
                backendStatus === 'online'
                  ? '#065f46'
                  : backendStatus === 'offline'
                  ? '#7f1d1d'
                  : '#1e293b',
              color:
                backendStatus === 'online'
                  ? '#6ee7b7'
                  : backendStatus === 'offline'
                  ? '#fca5a5'
                  : '#94a3b8',
            }}
          >
            {backendStatus === 'online'
              ? 'API Online'
              : backendStatus === 'offline'
              ? 'API Offline'
              : 'Connecting...'}
          </span>
        </div>
      </header>

      {/* Body */}
      <div style={styles.body}>
        {/* Left: product list */}
        <aside style={styles.leftPanel}>
          <ProductList items={plan?.items ?? []} />
        </aside>

        {/* Centre: 3D scene */}
        <main style={styles.centerPanel}>
          <TrailerScene plan={plan} trailer={selectedTrailer} />
        </main>

        {/* Right: controls + metrics */}
        <aside style={styles.rightPanel}>
          <div style={styles.rightPanelTop}>
            <ControlPanel
              scenarios={scenarios}
              trailers={trailers}
              isLoading={isLoading}
              onOptimize={handleOptimize}
              onTrailerChange={setSelectedTrailer}
              selectedTrailerId={selectedTrailer?.trailerId ?? ''}
              onImportExcel={handleImportExcel}
            />
          </div>
          <div style={styles.rightPanelBottom}>
            <div
              style={{
                padding: '10px 14px 6px',
                color: '#e2e8f0',
                fontWeight: 700,
                fontSize: 13,
                borderBottom: '1px solid #1e293b',
              }}
            >
              Metrics
            </div>
            <MetricsPanel
              metrics={plan?.metrics ?? null}
              trailer={selectedTrailer}
              totalWeightKg={plan?.totalWeightKg ?? 0}
              placedCount={plan?.placedCount ?? 0}
              totalCount={plan?.totalCount ?? 0}
            />
          </div>
        </aside>
      </div>

      {/* Toast notification */}
      {toast && (
        <div style={{ ...styles.toast, ...(toast.error ? {} : styles.toastSuccess) }}>
          {toast.message}
        </div>
      )}
    </div>
  );
}
