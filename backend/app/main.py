from __future__ import annotations

import json

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.data.scenarios import ALL_SCENARIOS, get_scenario
from app.models.schemas import (
    AnalyzeRequest,
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
    plan = pack_trailer(body.trailer, body.products)
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


@app.post("/api/analyze", response_model=LoadSafetyAnalysis)
def analyze(body: AnalyzeRequest) -> LoadSafetyAnalysis:
    return analyze_load_safety(body.trailer, body.products, body.plan, body.speeds_kmh)
