import { Canvas, useThree } from "@react-three/fiber";
import { Edges, Grid, Line, OrbitControls } from "@react-three/drei";
import { useCallback, useMemo } from "react";
import * as THREE from "three";
import type { LoadingPlan, PlacedBox, Trailer } from "../types/api";
import type { Vec3Mm } from "../utils/loadMetrics";

const MM = 0.001;

/** Dane: x = długość naczepy, y = szerokość, z = wysokość. Three.js: Y w górę → (x, z, y). */
function dataToScene(xMm: number, yMm: number, zMm: number): [number, number, number] {
  return [xMm * MM, zMm * MM, yMm * MM];
}

function CenterOfMassMarker({ comMm, markerRadiusM }: { comMm: Vec3Mm; markerRadiusM: number }) {
  const [px, py, pz] = dataToScene(comMm.x, comMm.y, comMm.z);
  const r = markerRadiusM;
  const ringGeom = useMemo(() => new THREE.TorusGeometry(r * 1.6, r * 0.14, 12, 48), [r]);
  const stemPoints = useMemo(
    () => [new THREE.Vector3(px, 0.01, pz), new THREE.Vector3(px, py, pz)] as [THREE.Vector3, THREE.Vector3],
    [px, py, pz],
  );
  return (
    <group raycast={() => {}}>
      <Line points={stemPoints} color="#f472b6" lineWidth={2} transparent opacity={0.75} depthTest={false} />
      <group position={[px, py, pz]}>
        <mesh renderOrder={999}>
          <sphereGeometry args={[r, 24, 24]} />
          <meshBasicMaterial color="#f472b6" toneMapped={false} depthTest={false} />
        </mesh>
        <mesh rotation={[Math.PI / 2, 0, 0]} geometry={ringGeom} renderOrder={998}>
          <meshBasicMaterial color="#fbcfe8" transparent opacity={0.95} depthTest={false} />
        </mesh>
        <mesh geometry={ringGeom} renderOrder={997}>
          <meshBasicMaterial color="#fbcfe8" transparent opacity={0.6} depthTest={false} />
        </mesh>
      </group>
    </group>
  );
}

/** Obrys podłogi naczepy (z=0) — widać „gdzie kończy się skrzynia” względem siatki. */
function TrailerFootprint({ trailer }: { trailer: Trailer }) {
  const L = trailer.length_mm * MM;
  const W = trailer.width_mm * MM;
  const yFloor = 0.008;
  const geom = useMemo(() => {
    const g = new THREE.BufferGeometry();
    const arr = new Float32Array([
      0, yFloor, 0,
      L, yFloor, 0,
      L, yFloor, W,
      0, yFloor, W,
    ]);
    g.setAttribute("position", new THREE.BufferAttribute(arr, 3));
    return g;
  }, [L, W, yFloor]);
  return (
    <lineLoop geometry={geom} raycast={() => {}}>
      <lineBasicMaterial color="#38bdf8" transparent opacity={0.85} depthWrite={false} />
    </lineLoop>
  );
}

function TrailerShell({
  trailer,
  transparent,
}: {
  trailer: Trailer;
  transparent: boolean;
}) {
  const L = trailer.length_mm * MM;
  const W = trailer.width_mm * MM;
  const H = trailer.height_mm * MM;
  const geom = useMemo(() => new THREE.BoxGeometry(L, H, W), [L, H, W]);
  const ref = useCallback((node: THREE.Mesh | null) => {
    if (node) node.raycast = () => {};
  }, []);
  const hullOpacity = transparent ? 0.26 : 0.42;
  return (
    <group position={[L / 2, H / 2, W / 2]}>
      <mesh ref={ref} geometry={geom}>
        <meshStandardMaterial
          color="#334155"
          metalness={0.15}
          roughness={0.5}
          transparent={transparent}
          opacity={hullOpacity}
          depthWrite={!transparent}
        />
        <Edges color="#e2e8f0" threshold={18} />
      </mesh>
    </group>
  );
}

function CargoBox({
  b,
  exploded,
  center,
  selected,
  onSelect,
}: {
  b: PlacedBox;
  exploded: boolean;
  center: THREE.Vector3;
  selected: boolean;
  onSelect: (box: PlacedBox) => void;
}) {
  const { gl } = useThree();
  const lx = b.length_mm * MM;
  const wy = b.width_mm * MM;
  const hz = b.height_mm * MM;
  const centerMm = {
    x: b.x_mm + b.length_mm / 2,
    y: b.y_mm + b.width_mm / 2,
    z: b.z_mm + b.height_mm / 2,
  };
  const pos = useMemo(() => {
    const [px, py, pz] = dataToScene(centerMm.x, centerMm.y, centerMm.z);
    const base = new THREE.Vector3(px, py, pz);
    if (!exploded) return base;
    const dir = base.clone().sub(center);
    if (dir.lengthSq() < 1e-8) return base;
    dir.normalize();
    return base.add(dir.multiplyScalar(0.35));
  }, [centerMm.x, centerMm.y, centerMm.z, exploded, center]);

  const color = b.unstable ? "#f97316" : b.color || "#3b82f6";
  const emissive = selected ? "#38bdf8" : b.unstable ? "#7c2d12" : "#000000";
  const emissiveIntensity = selected ? 0.45 : b.unstable ? 0.25 : 0;

  return (
    <mesh
      position={pos}
      onPointerDown={(e) => e.stopPropagation()}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(b);
      }}
      onPointerOver={() => {
        gl.domElement.style.cursor = "pointer";
      }}
      onPointerOut={() => {
        gl.domElement.style.cursor = "auto";
      }}
    >
      <boxGeometry args={[lx, hz, wy]} />
      <meshStandardMaterial
        color={color}
        metalness={0.15}
        roughness={0.55}
        emissive={emissive}
        emissiveIntensity={emissiveIntensity}
      />
    </mesh>
  );
}

export function TrailerViewport({
  trailer,
  plan,
  trailerTransparent,
  exploded,
  selectedInstanceId,
  onSelectBox,
  centerOfMassMm,
  requestedBoxCount,
}: {
  trailer: Trailer;
  plan: LoadingPlan | null;
  trailerTransparent: boolean;
  exploded: boolean;
  selectedInstanceId: string | null;
  onSelectBox: (box: PlacedBox | null) => void;
  centerOfMassMm: Vec3Mm | null;
  requestedBoxCount?: number;
}) {
  const center = useMemo(() => {
    const L = trailer.length_mm * MM;
    const W = trailer.width_mm * MM;
    const H = trailer.height_mm * MM;
    return new THREE.Vector3(L / 2, H / 2, W / 2);
  }, [trailer]);

  const boxes = plan?.boxes ?? [];
  const L = trailer.length_mm * MM;
  const W = trailer.width_mm * MM;
  const H = trailer.height_mm * MM;
  const maxDim = Math.max(L, W, H);

  return (
    <div className="absolute inset-0 overflow-hidden rounded-lg border border-line bg-[#0a0d12]">
      <Canvas
        shadows
        style={{ width: "100%", height: "100%", display: "block" }}
        camera={{ position: [L * 0.55, H * 1.35, W * 1.65], fov: 45 }}
        gl={{ antialias: true }}
        onPointerMissed={() => onSelectBox(null)}
      >
        <color attach="background" args={["#07090c"]} />
        <ambientLight intensity={0.45} />
        <directionalLight position={[L * 0.6, H * 2, W * 0.4]} intensity={1.1} castShadow shadow-mapSize-width={2048} shadow-mapSize-height={2048} />
        <TrailerFootprint trailer={trailer} />
        <TrailerShell trailer={trailer} transparent={trailerTransparent} />
        {boxes.map((b) => (
          <CargoBox
            key={b.instance_id}
            b={b}
            exploded={exploded}
            center={center}
            selected={b.instance_id === selectedInstanceId}
            onSelect={onSelectBox}
          />
        ))}
        {!exploded && centerOfMassMm && boxes.length > 0 && (
          <CenterOfMassMarker comMm={centerOfMassMm} markerRadiusM={Math.max(0.14, maxDim * 0.022)} />
        )}
        <Grid
          infiniteGrid
          fadeDistance={maxDim * 3}
          sectionSize={1}
          cellSize={0.25}
          sectionColor="#334155"
          cellColor="#1e293b"
          position={[L / 2, 0, W / 2]}
        />
        <OrbitControls makeDefault minDistance={2} maxDistance={maxDim * 4} target={[L / 2, H / 3, W / 2]} />
      </Canvas>
      <div className="pointer-events-none absolute left-3 top-3 max-w-[min(100%,22rem)] space-y-1 rounded bg-black/55 px-2 py-1.5 font-mono text-[11px] text-slate-400">
        <div className="text-slate-200">
          Naczepa: {Math.round(trailer.length_mm)} × {Math.round(trailer.width_mm)} × {Math.round(trailer.height_mm)} mm
        </div>
        <div className={requestedBoxCount != null && boxes.length !== requestedBoxCount ? "text-amber-300" : "text-slate-300"}>
          Skrzynki: {boxes.length}
          {requestedBoxCount != null && ` / ${requestedBoxCount} szt. (quantity)`}
        </div>
        <div className="text-slate-500">
          X = długość (przód x=0) · Z = szerokość · Y = wysokość
        </div>
        <div className="text-slate-500">
          Niebieski obrys = podłoga · jasne krawędzie = skrzynia · różowy = środek masy
        </div>
        <div>Obrót: LMB · Zoom: kółko · Pan: PPM · Klik: skrzynka</div>
      </div>
    </div>
  );
}
