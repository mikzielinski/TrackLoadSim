import React from 'react';
import { LoadingMetrics, Trailer } from '../types';

interface ProgressBarProps {
  value: number;
  max: number;
  color: string;
  label: string;
  unit?: string;
}

function ProgressBar({ value, max, color, label, unit = '%' }: ProgressBarProps): JSX.Element {
  const pct = Math.min(100, (value / max) * 100);
  const overLimit = value > max;

  return (
    <div style={{ marginBottom: 12 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: 4,
          fontSize: 12,
        }}
      >
        <span style={{ color: '#94a3b8' }}>{label}</span>
        <span
          style={{
            color: overLimit ? '#ef4444' : '#e2e8f0',
            fontWeight: overLimit ? 700 : 400,
          }}
        >
          {value.toFixed(1)}{unit === '%' ? '%' : ` / ${max.toFixed(0)} ${unit}`}
        </span>
      </div>
      <div
        style={{
          height: 8,
          borderRadius: 4,
          background: '#1e293b',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${pct}%`,
            borderRadius: 4,
            background: overLimit ? '#ef4444' : color,
            transition: 'width 0.4s ease',
          }}
        />
      </div>
    </div>
  );
}

interface MetricRowProps {
  label: string;
  value: string;
  highlight?: boolean;
}

function MetricRow({ label, value, highlight = false }: MetricRowProps): JSX.Element {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        padding: '5px 0',
        borderBottom: '1px solid #1e293b',
        fontSize: 12,
      }}
    >
      <span style={{ color: '#94a3b8' }}>{label}</span>
      <span style={{ color: highlight ? '#facc15' : '#e2e8f0', fontWeight: highlight ? 600 : 400 }}>
        {value}
      </span>
    </div>
  );
}

interface MetricsPanelProps {
  metrics: LoadingMetrics | null;
  trailer: Trailer | null;
  totalWeightKg: number;
  placedCount: number;
  totalCount: number;
}

export default function MetricsPanel({
  metrics,
  trailer,
  totalWeightKg,
  placedCount,
  totalCount,
}: MetricsPanelProps): JSX.Element {
  if (!metrics || !trailer) {
    return (
      <div
        style={{
          padding: 20,
          color: '#475569',
          textAlign: 'center',
          fontSize: 13,
        }}
      >
        Run the optimizer to see metrics.
      </div>
    );
  }

  const unplacedCount = totalCount - placedCount;

  return (
    <div
      style={{
        padding: '14px 14px',
        overflowY: 'auto',
        height: '100%',
      }}
    >
      {/* Section: Utilization */}
      <div style={{ marginBottom: 18 }}>
        <div
          style={{
            color: '#e2e8f0',
            fontWeight: 700,
            fontSize: 13,
            marginBottom: 10,
            borderBottom: '1px solid #1e293b',
            paddingBottom: 6,
          }}
        >
          Utilization
        </div>
        <ProgressBar
          label="Volume Utilization"
          value={metrics.volumeUtilizationPct}
          max={100}
          color="#3b82f6"
          unit="%"
        />
        <ProgressBar
          label="Weight Utilization"
          value={metrics.weightUtilizationPct}
          max={100}
          color="#8b5cf6"
          unit="%"
        />
      </div>

      {/* Section: Axle Loads */}
      <div style={{ marginBottom: 18 }}>
        <div
          style={{
            color: '#e2e8f0',
            fontWeight: 700,
            fontSize: 13,
            marginBottom: 10,
            borderBottom: '1px solid #1e293b',
            paddingBottom: 6,
          }}
        >
          Axle Loads
        </div>
        <ProgressBar
          label="Front Axle"
          value={metrics.frontAxleLoadKg}
          max={trailer.axleLoadLimits.frontKg}
          color="#10b981"
          unit="kg"
        />
        <ProgressBar
          label="Rear Axle"
          value={metrics.rearAxleLoadKg}
          max={trailer.axleLoadLimits.rearKg}
          color="#f59e0b"
          unit="kg"
        />
      </div>

      {/* Section: Summary metrics */}
      <div style={{ marginBottom: 18 }}>
        <div
          style={{
            color: '#e2e8f0',
            fontWeight: 700,
            fontSize: 13,
            marginBottom: 10,
            borderBottom: '1px solid #1e293b',
            paddingBottom: 6,
          }}
        >
          Summary
        </div>
        <MetricRow
          label="Total Weight"
          value={`${totalWeightKg.toFixed(1)} / ${trailer.maxWeightKg.toFixed(0)} kg`}
        />
        <MetricRow
          label="Items Placed"
          value={`${placedCount} / ${totalCount}`}
          highlight={unplacedCount > 0}
        />
        {unplacedCount > 0 && (
          <MetricRow
            label="Items Not Placed"
            value={String(unplacedCount)}
            highlight
          />
        )}
        <MetricRow
          label="Stability Score"
          value={`${metrics.stabilityScore.toFixed(1)} / 100`}
          highlight={metrics.stabilityScore < 60}
        />
      </div>

      {/* Section: Center of Gravity */}
      <div style={{ marginBottom: 18 }}>
        <div
          style={{
            color: '#e2e8f0',
            fontWeight: 700,
            fontSize: 13,
            marginBottom: 10,
            borderBottom: '1px solid #1e293b',
            paddingBottom: 6,
          }}
        >
          Center of Gravity
        </div>
        <MetricRow label="CoG X (Length)" value={`${metrics.centerOfGravity.xMm.toFixed(0)} mm`} />
        <MetricRow label="CoG Y (Width)" value={`${metrics.centerOfGravity.yMm.toFixed(0)} mm`} />
        <MetricRow label="CoG Z (Height)" value={`${metrics.centerOfGravity.zMm.toFixed(0)} mm`} />
      </div>

      {/* Section: Warnings */}
      {metrics.warnings.length > 0 && (
        <div>
          <div
            style={{
              color: '#ef4444',
              fontWeight: 700,
              fontSize: 13,
              marginBottom: 10,
              borderBottom: '1px solid #7f1d1d',
              paddingBottom: 6,
            }}
          >
            Warnings ({metrics.warnings.length})
          </div>
          {metrics.warnings.map((w, i) => (
            <div
              key={i}
              style={{
                background: 'rgba(127,29,29,0.25)',
                border: '1px solid #7f1d1d',
                borderRadius: 6,
                padding: '7px 10px',
                marginBottom: 6,
                fontSize: 11,
                color: '#fca5a5',
                lineHeight: 1.4,
              }}
            >
              {w}
            </div>
          ))}
        </div>
      )}

      {metrics.warnings.length === 0 && (
        <div
          style={{
            background: 'rgba(6,78,59,0.25)',
            border: '1px solid #065f46',
            borderRadius: 6,
            padding: '8px 12px',
            fontSize: 12,
            color: '#6ee7b7',
            textAlign: 'center',
          }}
        >
          All constraints satisfied
        </div>
      )}
    </div>
  );
}
