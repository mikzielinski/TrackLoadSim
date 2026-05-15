from __future__ import annotations

import json

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.data.scenarios import ALL_SCENARIOS, get_scenario
from app.models.schemas import (
    AiConnectionStatus,
    AiOptimizeRequest,
    AiOptimizeResponse,
    AiStatusRequest,
    AnalyzeRequest,
    ExportLoadMapPdfRequest,
    LoadSafetyAnalysis,
    LoadingPlan,
    OptimizeRequest,
    OptimizeResponse,
    PhysicsValidationResult,
    Scenario,
)
from app.optimizer import pack_trailer
from app.physics import validate_static_drop
from app.physics.dynamics_analysis import analyze_load_safety
from app.services.excel_import import parse_csv_text, parse_excel
from app.services.ai_optimizer import (
    pack_with_guidance,
    request_packing_guidance,
    verify_ai_connection,
)
from app.services.load_map_pdf import build_load_map_pdf

app = FastAPI(title="TrackLoadSim API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/scenarios")
def list_scenarios() -> list[dict[str, str]]:
    return [{"scenario_id": s.scenario_id, "title": s.title} for s in ALL_SCENARIOS]


@app.get("/api/scenarios/{scenario_id}", response_model=Scenario)
def read_scenario(scenario_id: str) -> Scenario:
    s = get_scenario(scenario_id)
    if not s:
        raise HTTPException(404, "Unknown scenario")
    return s


@app.post("/api/optimize", response_model=OptimizeResponse)
def optimize(body: OptimizeRequest) -> OptimizeResponse:
    plan = pack_trailer(body.trailer, body.products, mode=body.mode)
    if body.run_physics and plan.boxes:
        physics = validate_static_drop(body.trailer, plan.boxes)
    else:
        physics = PhysicsValidationResult(
            ok=True,
            mode="skipped",
            message="Brak skrzynek lub wyłączona walidacja PyBullet.",
            steps_simulated=0,
        )
    return OptimizeResponse(plan=plan, physics=physics)


@app.post("/api/import/products")
async def import_products(file: UploadFile = File(...)) -> Scenario:
    raw = await file.read()
    name = (file.filename or "").lower()
    if name.endswith(".xlsx") or name.endswith(".xlsm"):
        trailer, products = parse_excel(raw)
    elif name.endswith(".csv"):
        trailer, products = parse_csv_text(raw.decode("utf-8-sig", errors="replace"))
    else:
        raise HTTPException(400, "Upload .xlsx or .csv")
    if not products:
        raise HTTPException(400, "No product rows parsed")
    plan = pack_trailer(trailer, products)
    physics = validate_static_drop(trailer, plan.boxes) if plan.boxes else None
    warn = list(plan.warnings)
    if physics is not None and not physics.ok and physics.mode == "pybullet":
        warn.append(f"Physics check: {physics.message}")
    plan = LoadingPlan(**{**plan.model_dump(), "warnings": warn})
    return Scenario(
        scenario_id="IMPORTED",
        title=f"Import: {file.filename}",
        description="Loaded from spreadsheet; placements from greedy packer.",
        trailer=trailer,
        products=products,
        plan=plan,
    )


@app.post("/api/export/plan")
def export_plan(plan: LoadingPlan) -> dict[str, str]:
    return {"json": json.dumps(plan.model_dump(), indent=2)}


@app.post("/api/export/load-map-pdf")
def export_load_map_pdf(body: ExportLoadMapPdfRequest) -> Response:
    if not body.plan.boxes:
        raise HTTPException(400, "Plan nie zawiera skrzynek — najpierw przelicz rozmieszczenie.")
    pdf = build_load_map_pdf(body.trailer, body.plan, body.title)
    fname = f"mapa-zaladunku-{body.scenario_id or 'plan'}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.post("/api/analyze", response_model=LoadSafetyAnalysis)
def analyze(body: AnalyzeRequest) -> LoadSafetyAnalysis:
    return analyze_load_safety(body.trailer, body.products, body.plan, body.speeds_kmh)


@app.post("/api/ai/verify", response_model=AiConnectionStatus)
def ai_verify(body: AiStatusRequest | None = None) -> AiConnectionStatus:
    key = body.api_key if body else None
    return verify_ai_connection(key)


@app.post("/api/ai/optimize", response_model=AiOptimizeResponse)
def ai_optimize(body: AiOptimizeRequest) -> AiOptimizeResponse:
    connection = verify_ai_connection(body.api_key)
    if not connection.connected:
        raise HTTPException(503, connection.message)

    baseline = body.baseline_plan or pack_trailer(body.trailer, body.products, mode="greedy")
    safety = analyze_load_safety(body.trailer, body.products, baseline, [50, 80, 90])
    rec_items: list[str] = []
    if safety.recommendations:
        rec_items.extend(safety.recommendations.loading.items[:4])
        rec_items.extend(safety.recommendations.driving.items[:3])
    rec_items.extend(safety.notes[:4])

    try:
        guidance = request_packing_guidance(
            body.trailer,
            body.products,
            baseline=baseline,
            safety_notes=list(baseline.warnings) + list(safety.notes),
            recommendation_items=rec_items,
            user_notes=body.user_notes,
            api_key_override=body.api_key,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Błąd AI: {exc}") from exc

    plan = pack_with_guidance(body.trailer, body.products, guidance)
    if body.run_physics and plan.boxes:
        physics = validate_static_drop(body.trailer, plan.boxes)
    else:
        physics = PhysicsValidationResult(
            ok=True,
            mode="skipped",
            message="Brak skrzynek lub wyłączona walidacja PyBullet.",
            steps_simulated=0,
        )
    safety = analyze_load_safety(body.trailer, body.products, plan, [50, 80, 90])
    if guidance.loading_tips and safety.recommendations:
        rec = safety.recommendations
        ai_items = [f"AI: {t}" for t in guidance.loading_tips[:4]]
        loading = rec.loading.model_copy(update={"items": [*ai_items, *rec.loading.items][:8]})
        safety = safety.model_copy(update={"recommendations": rec.model_copy(update={"loading": loading})})
    return AiOptimizeResponse(
        plan=plan,
        physics=physics,
        guidance=guidance,
        connection=connection,
        safety_analysis=safety,
    )
