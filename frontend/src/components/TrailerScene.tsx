import React, { useRef, useState, useMemo } from 'react';
import { Canvas, ThreeEvent } from '@react-three/fiber';
import { OrbitControls, Grid, Line } from '@react-three/drei';
import * as THREE from 'three';
import { LoadingPlan, PlacedItem, Trailer } from '../types';

// ---------------------------------------------------------------------------
// Colour mapping by stacking group / fragility
// ---------------------------------------------------------------------------

function itemColor(item: PlacedItem): string {
  if (item.fragile) return '#ef4444'; // red
  switch (item.stackingGroup) {
    case 'heavy':
    case 'hazmat':
      return '#f97316'; // orange
    case 'electronics':
      return '#8b5cf6'; // purple
    case 'paper':
      return '#84cc16'; // lime
    case 'soft':
    case 'clothing':
      return '#22d3ee'; // cyan
    case 'tools':
      return '#eab308'; // yellow
    case 'fragile':
      return '#ef4444'; // red
    case 'furniture':
      return '#a3a3a3'; // gray
    case 'sports':
      return '#10b981'; // emerald
    default:
      return '#3b82f6'; // blue
  }
}

// ---------------------------------------------------------------------------
// Tooltip state
// ---------------------------------------------------------------------------

interface TooltipData {
  item: PlacedItem;
  screenX: number;
  screenY: number;
}

// ---------------------------------------------------------------------------
// Single cargo box component
// ---------------------------------------------------------------------------

interface CargoBoxProps {
  item: PlacedItem;
  scale: number;
  onHover: (data: TooltipData | null) => void;
}

function CargoBox({ item, scale, onHover }: CargoBoxProps): JSX.Element {
  const [hovered, setHovered] = useState(false);
  const color = itemColor(item);

  const sx = item.lengthMm * scale;
  const sy = item.heightMm * scale;
  const sz = item.widthMm * scale;

  // Position centre of box in Three.js coords (Y = up)
  const px = (item.xMm + item.lengthMm / 2) * scale;
  const py = (item.zMm + item.heightMm / 2) * scale;
  const pz = (item.yMm + item.widthMm / 2) * scale;

  const handlePointerOver = (e: ThreeEvent<PointerEvent>): void => {
    e.stopPropagation();
    setHovered(true);
    onHover({
      item,
      screenX: e.clientX,
      screenY: e.clientY,
    });
  };

  const handlePointerOut = (): void => {
    setHovered(false);
    onHover(null);
  };

  return (
    <group position={[px, py, pz]}>
      <mesh
        onPointerOver={handlePointerOver}
        onPointerOut={handlePointerOut}
        castShadow
        receiveShadow
      >
        <boxGeometry args={[sx, sy, sz]} />
        <meshStandardMaterial
          color={color}
          transparent
          opacity={hovered ? 0.95 : 0.82}
          roughness={0.6}
          metalness={0.1}
        />
      </mesh>
      {/* Wireframe outline */}
      <lineSegments>
        <edgesGeometry args={[new THREE.BoxGeometry(sx, sy, sz)]} />
        <lineBasicMaterial color={hovered ? '#ffffff' : '#000000'} linewidth={1} />
      </lineSegments>
    </group>
  );
}

// ---------------------------------------------------------------------------
// Trailer wireframe
// ---------------------------------------------------------------------------

interface TrailerWireframeProps {
  trailer: Trailer;
  scale: number;
}

function TrailerWireframe({ trailer, scale }: TrailerWireframeProps): JSX.Element {
  const lx = trailer.lengthMm * scale;
  const ly = trailer.heightMm * scale;
  const lz = trailer.widthMm * scale;

  return (
    <group position={[lx / 2, ly / 2, lz / 2]}>
      {/* Semi-transparent fill */}
      <mesh>
        <boxGeometry args={[lx, ly, lz]} />
        <meshStandardMaterial
          color="#334155"
          transparent
          opacity={0.08}
          side={THREE.BackSide}
        />
      </mesh>
      {/* Wireframe edges */}
      <lineSegments>
        <edgesGeometry args={[new THREE.BoxGeometry(lx, ly, lz)]} />
        <lineBasicMaterial color="#94a3b8" linewidth={2} />
      </lineSegments>
    </group>
  );
}

// ---------------------------------------------------------------------------
// CoG sphere
// ---------------------------------------------------------------------------

interface CoGSphereProps {
  xMm: number;
  yMm: number;
  zMm: number;
  scale: number;
}

function CoGSphere({ xMm, yMm, zMm, scale }: CoGSphereProps): JSX.Element {
  return (
    <mesh position={[xMm * scale, zMm * scale, yMm * scale]}>
      <sphereGeometry args={[0.12, 16, 16]} />
      <meshStandardMaterial color="#facc15" emissive="#fbbf24" emissiveIntensity={0.6} />
    </mesh>
  );
}

// ---------------------------------------------------------------------------
// Main scene component
// ---------------------------------------------------------------------------

interface TrailerSceneProps {
  plan: LoadingPlan | null;
  trailer: Trailer | null;
}

export default function TrailerScene({ plan, trailer }: TrailerSceneProps): JSX.Element {
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);

  // Scale factor: convert mm to Three.js units (1 unit = 1000 mm = 1 m)
  const SCALE = 0.001;

  const activeTrailer = useMemo<Trailer | null>(() => {
    if (plan && !trailer) {
      // Fallback placeholder trailer dimensions derived from plan items
      return null;
    }
    return trailer;
  }, [plan, trailer]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <Canvas
        camera={{ position: [8, 5, 8], fov: 50, near: 0.01, far: 500 }}
        shadows
        style={{ background: '#0f172a' }}
      >
        {/* Lighting */}
        <ambientLight intensity={0.5} />
        <directionalLight
          position={[10, 20, 10]}
          intensity={1.2}
          castShadow
          shadow-mapSize-width={2048}
          shadow-mapSize-height={2048}
        />
        <directionalLight position={[-10, 10, -10]} intensity={0.4} />

        {/* Ground grid */}
        <Grid
          position={[0, -0.001, 0]}
          args={[20, 20]}
          cellSize={1}
          cellThickness={0.5}
          cellColor="#1e293b"
          sectionSize={5}
          sectionThickness={1}
          sectionColor="#334155"
          fadeDistance={50}
          fadeStrength={1}
          infiniteGrid
        />

        {/* Trailer wireframe */}
        {activeTrailer && <TrailerWireframe trailer={activeTrailer} scale={SCALE} />}

        {/* Cargo items */}
        {plan?.items.map((item, idx) => (
          <CargoBox
            key={`${item.productId}-${idx}`}
            item={item}
            scale={SCALE}
            onHover={setTooltip}
          />
        ))}

        {/* Center of gravity */}
        {plan && plan.items.length > 0 && (
          <CoGSphere
            xMm={plan.metrics.centerOfGravity.xMm}
            yMm={plan.metrics.centerOfGravity.yMm}
            zMm={plan.metrics.centerOfGravity.zMm}
            scale={SCALE}
          />
        )}

        <OrbitControls
          enableDamping
          dampingFactor={0.05}
          minDistance={1}
          maxDistance={100}
          target={
            activeTrailer
              ? [
                  (activeTrailer.lengthMm * SCALE) / 2,
                  (activeTrailer.heightMm * SCALE) / 2,
                  (activeTrailer.widthMm * SCALE) / 2,
                ]
              : [0, 0, 0]
          }
        />
      </Canvas>

      {/* Tooltip overlay */}
      {tooltip && (
        <div
          style={{
            position: 'fixed',
            left: tooltip.screenX + 12,
            top: tooltip.screenY - 10,
            background: 'rgba(15,23,42,0.95)',
            border: '1px solid #475569',
            borderRadius: 8,
            padding: '10px 14px',
            pointerEvents: 'none',
            zIndex: 1000,
            minWidth: 220,
          }}
        >
          <div style={{ color: '#f1f5f9', fontWeight: 700, marginBottom: 4 }}>
            {tooltip.item.name}
          </div>
          <div style={{ color: '#94a3b8', fontSize: 12, lineHeight: 1.8 }}>
            <div>
              Dims: {tooltip.item.lengthMm}×{tooltip.item.widthMm}×{tooltip.item.heightMm} mm
            </div>
            <div>Weight: {tooltip.item.weightKg} kg</div>
            <div>
              Position: X={tooltip.item.xMm.toFixed(0)} Y={tooltip.item.yMm.toFixed(0)} Z=
              {tooltip.item.zMm.toFixed(0)} mm
            </div>
            <div>Orientation: {tooltip.item.orientation}</div>
            <div>Group: {tooltip.item.stackingGroup}</div>
            {tooltip.item.fragile && (
              <div style={{ color: '#ef4444', fontWeight: 600 }}>FRAGILE</div>
            )}
          </div>
        </div>
      )}

      {/* Legend */}
      <div
        style={{
          position: 'absolute',
          bottom: 16,
          left: 16,
          background: 'rgba(15,23,42,0.85)',
          border: '1px solid #334155',
          borderRadius: 8,
          padding: '8px 12px',
          fontSize: 11,
          color: '#94a3b8',
        }}
      >
        <div style={{ fontWeight: 700, color: '#e2e8f0', marginBottom: 6 }}>Legend</div>
        {[
          { color: '#ef4444', label: 'Fragile' },
          { color: '#f97316', label: 'Heavy / Hazmat' },
          { color: '#8b5cf6', label: 'Electronics' },
          { color: '#3b82f6', label: 'General' },
          { color: '#22d3ee', label: 'Soft / Clothing' },
          { color: '#84cc16', label: 'Paper' },
          { color: '#eab308', label: 'Tools' },
          { color: '#facc15', label: 'CoG marker' },
        ].map(({ color, label }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
            <div
              style={{
                width: 12,
                height: 12,
                borderRadius: 2,
                background: color,
                flexShrink: 0,
              }}
            />
            <span>{label}</span>
          </div>
        ))}
      </div>

      {/* Empty state */}
      {!plan && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            pointerEvents: 'none',
          }}
        >
          <div
            style={{
              textAlign: 'center',
              color: '#475569',
            }}
          >
            <div style={{ fontSize: 48, marginBottom: 12 }}>&#9646;&#9646;&#9646;</div>
            <div style={{ fontSize: 18, fontWeight: 600 }}>No loading plan yet</div>
            <div style={{ fontSize: 14, marginTop: 6 }}>Select a scenario and click Optimize</div>
          </div>
        </div>
      )}
    </div>
  );
}
