import React, { useMemo, useState } from 'react';
import { PlacedItem } from '../types';

type SortKey = 'name' | 'weightKg' | 'stackingGroup';
type SortDir = 'asc' | 'desc';

interface ProductListProps {
  items: PlacedItem[];
}

const thStyle: React.CSSProperties = {
  padding: '8px 10px',
  textAlign: 'left',
  color: '#94a3b8',
  fontWeight: 600,
  fontSize: 12,
  borderBottom: '1px solid #1e293b',
  whiteSpace: 'nowrap',
  cursor: 'pointer',
  userSelect: 'none',
};

const tdStyle: React.CSSProperties = {
  padding: '7px 10px',
  fontSize: 12,
  color: '#e2e8f0',
  borderBottom: '1px solid #1e293b',
  whiteSpace: 'nowrap',
};

export default function ProductList({ items }: ProductListProps): JSX.Element {
  const [filter, setFilter] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('name');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  const handleSort = (key: SortKey): void => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sortArrow = (key: SortKey): string => {
    if (sortKey !== key) return ' ';
    return sortDir === 'asc' ? ' ▲' : ' ▼';
  };

  const filtered = useMemo(() => {
    const q = filter.toLowerCase();
    return items
      .filter(
        (i) =>
          i.name.toLowerCase().includes(q) ||
          i.stackingGroup.toLowerCase().includes(q),
      )
      .sort((a, b) => {
        let valA: string | number;
        let valB: string | number;

        if (sortKey === 'name') {
          valA = a.name;
          valB = b.name;
        } else if (sortKey === 'weightKg') {
          valA = a.weightKg;
          valB = b.weightKg;
        } else {
          valA = a.stackingGroup;
          valB = b.stackingGroup;
        }

        if (valA < valB) return sortDir === 'asc' ? -1 : 1;
        if (valA > valB) return sortDir === 'asc' ? 1 : -1;
        return 0;
      });
  }, [items, filter, sortKey, sortDir]);

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '12px 14px',
          borderBottom: '1px solid #1e293b',
          flexShrink: 0,
        }}
      >
        <div style={{ color: '#e2e8f0', fontWeight: 700, fontSize: 14, marginBottom: 8 }}>
          Placed Items ({items.length})
        </div>
        <input
          type="text"
          placeholder="Filter by name or group..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{
            width: '100%',
            padding: '6px 10px',
            background: '#1e293b',
            border: '1px solid #334155',
            borderRadius: 6,
            color: '#e2e8f0',
            fontSize: 12,
            outline: 'none',
          }}
        />
      </div>

      {/* Table */}
      <div style={{ overflowY: 'auto', flex: 1 }}>
        {items.length === 0 ? (
          <div
            style={{
              padding: 24,
              textAlign: 'center',
              color: '#475569',
              fontSize: 13,
            }}
          >
            No items placed yet.
            <br />
            Run optimizer to see results.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ position: 'sticky', top: 0, background: '#0f172a', zIndex: 1 }}>
              <tr>
                <th style={thStyle} onClick={() => handleSort('name')}>
                  Name{sortArrow('name')}
                </th>
                <th style={{ ...thStyle, textAlign: 'right' }}>Dims (mm)</th>
                <th
                  style={{ ...thStyle, textAlign: 'right' }}
                  onClick={() => handleSort('weightKg')}
                >
                  Wt (kg){sortArrow('weightKg')}
                </th>
                <th style={thStyle} onClick={() => handleSort('stackingGroup')}>
                  Group{sortArrow('stackingGroup')}
                </th>
                <th style={{ ...thStyle, textAlign: 'center' }}>Flags</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item, idx) => (
                <tr
                  key={`${item.productId}-${idx}`}
                  style={{
                    background: idx % 2 === 0 ? 'transparent' : 'rgba(30,41,59,0.4)',
                  }}
                >
                  <td style={tdStyle}>{item.name}</td>
                  <td style={{ ...tdStyle, textAlign: 'right', color: '#94a3b8' }}>
                    {item.lengthMm.toFixed(0)}×{item.widthMm.toFixed(0)}×
                    {item.heightMm.toFixed(0)}
                  </td>
                  <td style={{ ...tdStyle, textAlign: 'right' }}>{item.weightKg}</td>
                  <td style={{ ...tdStyle, color: '#94a3b8' }}>{item.stackingGroup}</td>
                  <td style={{ ...tdStyle, textAlign: 'center' }}>
                    {item.fragile && (
                      <span
                        style={{
                          background: '#7f1d1d',
                          color: '#fca5a5',
                          borderRadius: 4,
                          padding: '1px 5px',
                          fontSize: 10,
                          fontWeight: 700,
                        }}
                      >
                        FRAGILE
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
