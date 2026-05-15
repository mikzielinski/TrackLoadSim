"""Optional PyBullet static drop check for placed boxes."""

from __future__ import annotations

import math

from app.models.schemas import PhysicsValidationResult, PlacedBox, Trailer


def _pybullet_data_path() -> str:
    try:
        import pybullet_data  # type: ignore

        return pybullet_data.getDataPath()
    except Exception:
        return ""


def validate_static_drop(trailer: Trailer, boxes: list[PlacedBox], steps: int = 240) -> PhysicsValidationResult:
    try:
        import pybullet as p  # type: ignore
    except Exception as e:  # noqa: BLE001
        return PhysicsValidationResult(
            ok=True,
            mode="skipped",
            message=f"PyBullet niedostępny — zainstaluj: pip install pybullet ({e!s}).",
            steps_simulated=0,
        )

    if not boxes:
        return PhysicsValidationResult(ok=True, mode="skipped", message="Brak skrzynek do symulacji.", steps_simulated=0)

    cid = p.connect(p.DIRECT)
    scale = 1 / 1000.0
    try:
        p.setGravity(0, 0, -9.81)
        data_path = _pybullet_data_path()
        if data_path:
            p.setAdditionalSearchPath(data_path)

        lx = trailer.length_mm * scale
        wy = trailer.width_mm * scale
        floor_half = [lx / 2, wy / 2, 0.02]
        floor_shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=floor_half)
        p.createMultiBody(0, floor_shape, basePosition=[lx / 2, wy / 2, -0.02])

        body_ids: list[int] = []
        for b in boxes:
            hx = b.length_mm * scale / 2
            hy = b.width_mm * scale / 2
            hz = b.height_mm * scale / 2
            sh = p.createCollisionShape(p.GEOM_BOX, halfExtents=[hx, hy, hz])
            cx = (b.x_mm + b.length_mm / 2) * scale
            cy = (b.y_mm + b.width_mm / 2) * scale
            cz = (b.z_mm + b.height_mm / 2) * scale
            mass = max(b.weight_kg, 1.0)
            bid = p.createMultiBody(mass, sh, basePosition=[cx, cy, cz + hz + 0.01])
            p.changeDynamics(bid, -1, lateralFriction=0.75, restitution=0.05)
            body_ids.append(bid)

        for _ in range(steps):
            p.stepSimulation()

        max_pen = 0.0
        max_slide = 0.0
        for bid, b in zip(body_ids, boxes, strict=True):
            pos, _orn = p.getBasePositionAndOrientation(bid)
            exp_cx = (b.x_mm + b.length_mm / 2) * scale
            exp_cy = (b.y_mm + b.width_mm / 2) * scale
            exp_cz = (b.z_mm + b.height_mm / 2) * scale
            max_pen = max(max_pen, abs(pos[2] - exp_cz))
            max_slide = max(max_slide, math.hypot(pos[0] - exp_cx, pos[1] - exp_cy))

        ok = max_pen < 0.15 and max_slide < 0.12
        msg = f"Symulacja statyczna: odsunięcie pion. {max_pen:.2f} m, w planie {max_slide:.2f} m"
        return PhysicsValidationResult(ok=ok, mode="pybullet", message=msg, steps_simulated=steps)
    except Exception as e:  # noqa: BLE001
        return PhysicsValidationResult(ok=False, mode="error", message=str(e), steps_simulated=0)
    finally:
        p.disconnect(cid)
