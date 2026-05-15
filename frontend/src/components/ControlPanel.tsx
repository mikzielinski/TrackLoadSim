import React, { useEffect, useState } from 'react';
import { ScenarioInfo, Trailer } from '../types';
import api from '../services/api';

interface ControlPanelProps {
  scenarios: ScenarioInfo[];
  trailers: Trailer[];
  isLoading: boolean;
  onOptimize: (scenarioName: string) => void;
  onTrailerChange: (trailer: Trailer) => void;
  selectedTrailerId: string;
  onImportExcel: (file: File) => void;
}

const SCENARIO_LABELS: Record<string, string> = {
  half_loaded: 'Half Loaded (~50%)',
  fully_optimized: 'Fully Optimized (85%+)',
  overloaded: 'Overloaded (Weight Exceeded)',
  fragile: 'Fragile Goods Only',
  mixed_cargo: 'Mixed Cargo (Retail)',
};

export default function ControlPanel({
  scenarios,
  trailers,
  isLoading,
  onOptimize,
  onTrailerChange,
  selectedTrailerId,
  onImportExcel,
}: ControlPanelProps): JSX.Element {
  const [selectedScenario, setSelectedScenario] = useState<string>('');
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (scenarios.length > 0 && !selectedScenario) {
      setSelectedScenario(scenarios[0].name);
    }
  }, [scenarios, selectedScenario]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const file = e.target.files?.[0];
    if (file) {
      onImportExcel(file);
      // Reset input so the same file can be re-uploaded
      e.target.value = '';
    }
  };

  const selectedScenarioInfo = scenarios.find((s) => s.name === selectedScenario);

  return (
    <div style={{ padding: '14px 14px' }}>
      {/* Title */}
      <div
        style={{
          color: '#e2e8f0',
          fontWeight: 700,
          fontSize: 14,
          marginBottom: 16,
          borderBottom: '1px solid #1e293b',
          paddingBottom: 8,
        }}
      >
        Configuration
      </div>

      {/* Trailer selector */}
      <div style={{ marginBottom: 14 }}>
        <label
          style={{
            display: 'block',
            color: '#94a3b8',
            fontSize: 11,
            fontWeight: 600,
            marginBottom: 5,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          Trailer
        </label>
        <select
          value={selectedTrailerId}
          onChange={(e) => {
            const t = trailers.find((tr) => tr.trailerId === e.target.value);
            if (t) onTrailerChange(t);
          }}
          style={{
            width: '100%',
            padding: '8px 10px',
            background: '#1e293b',
            border: '1px solid #334155',
            borderRadius: 6,
            color: '#e2e8f0',
            fontSize: 12,
            outline: 'none',
            cursor: 'pointer',
          }}
        >
          {trailers.map((t) => (
            <option key={t.trailerId} value={t.trailerId}>
              {t.name}
            </option>
          ))}
        </select>
      </div>

      {/* Scenario selector */}
      <div style={{ marginBottom: 14 }}>
        <label
          style={{
            display: 'block',
            color: '#94a3b8',
            fontSize: 11,
            fontWeight: 600,
            marginBottom: 5,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          Scenario
        </label>
        <select
          value={selectedScenario}
          onChange={(e) => setSelectedScenario(e.target.value)}
          style={{
            width: '100%',
            padding: '8px 10px',
            background: '#1e293b',
            border: '1px solid #334155',
            borderRadius: 6,
            color: '#e2e8f0',
            fontSize: 12,
            outline: 'none',
            cursor: 'pointer',
          }}
        >
          {scenarios.map((s) => (
            <option key={s.name} value={s.name}>
              {SCENARIO_LABELS[s.name] ?? s.name}
            </option>
          ))}
        </select>
        {selectedScenarioInfo && (
          <div
            style={{
              marginTop: 6,
              fontSize: 11,
              color: '#64748b',
              lineHeight: 1.4,
            }}
          >
            {selectedScenarioInfo.description}
          </div>
        )}
      </div>

      {/* Optimize button */}
      <button
        disabled={isLoading || !selectedScenario}
        onClick={() => onOptimize(selectedScenario)}
        style={{
          width: '100%',
          padding: '11px 0',
          background: isLoading ? '#1e3a5f' : '#2563eb',
          color: isLoading ? '#93c5fd' : '#ffffff',
          border: 'none',
          borderRadius: 8,
          fontWeight: 700,
          fontSize: 14,
          cursor: isLoading ? 'not-allowed' : 'pointer',
          marginBottom: 10,
          transition: 'background 0.2s',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
        }}
      >
        {isLoading ? (
          <>
            <Spinner />
            Optimizing...
          </>
        ) : (
          'Optimize Loading'
        )}
      </button>

      {/* Excel import */}
      <div style={{ marginTop: 16, borderTop: '1px solid #1e293b', paddingTop: 14 }}>
        <div
          style={{
            color: '#e2e8f0',
            fontWeight: 700,
            fontSize: 13,
            marginBottom: 10,
          }}
        >
          Import Products
        </div>
        <button
          onClick={() => fileInputRef.current?.click()}
          style={{
            width: '100%',
            padding: '9px 0',
            background: '#0f172a',
            color: '#94a3b8',
            border: '1px dashed #334155',
            borderRadius: 8,
            fontSize: 12,
            cursor: 'pointer',
            transition: 'border-color 0.2s',
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.borderColor = '#3b82f6';
            (e.currentTarget as HTMLButtonElement).style.color = '#93c5fd';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.borderColor = '#334155';
            (e.currentTarget as HTMLButtonElement).style.color = '#94a3b8';
          }}
        >
          Upload Excel (.xlsx)
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        <div style={{ fontSize: 10, color: '#475569', marginTop: 5, textAlign: 'center' }}>
          Required columns: name, lengthMm, widthMm, heightMm, weightKg, quantity
        </div>
      </div>
    </div>
  );
}

function Spinner(): JSX.Element {
  const [angle, setAngle] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setAngle((a) => (a + 30) % 360), 80);
    return () => clearInterval(id);
  }, []);

  return (
    <div
      style={{
        width: 14,
        height: 14,
        border: '2px solid transparent',
        borderTopColor: '#93c5fd',
        borderRadius: '50%',
        transform: `rotate(${angle}deg)`,
      }}
    />
  );
}
