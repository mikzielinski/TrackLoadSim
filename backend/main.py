"""
TrackLoadSim — FastAPI backend entry point.
"""
from __future__ import annotations

import io
import uuid
from typing import Any, Dict, List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models.loading_plan import LoadingPlan
from models.product import PhysicsProperties, Product
from models.trailer import AxleLimits, Trailer
from optimizer.packer import Packer3D
from scenarios.demo_data import SCENARIOS, get_scenario, list_scenarios

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="TrackLoadSim API",
    description="AI-assisted trailer loading optimization API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

packer = Packer3D()

# ---------------------------------------------------------------------------
# Static data
# ---------------------------------------------------------------------------

AVAILABLE_TRAILERS: List[Trailer] = [
    Trailer(
        trailerId="T-STD-001",
        name="Standard Semi-Trailer 13.6m",
        lengthMm=13600.0,
        widthMm=2400.0,
        heightMm=2700.0,
        maxWeightKg=24000.0,
        maxStackHeightMm=2700.0,
        axleLoadLimits=AxleLimits(frontKg=7100.0, rearKg=11500.0),
    ),
    Trailer(
        trailerId="T-MEGA-002",
        name="Mega-Liner 13.6m High Cube",
        lengthMm=13600.0,
        widthMm=2480.0,
        heightMm=3000.0,
        maxWeightKg=26000.0,
        maxStackHeightMm=3000.0,
        axleLoadLimits=AxleLimits(frontKg=7500.0, rearKg=12500.0),
    ),
    Trailer(
        trailerId="T-BOX-003",
        name="Box Trailer 7.2m",
        lengthMm=7200.0,
        widthMm=2400.0,
        heightMm=2400.0,
        maxWeightKg=10000.0,
        maxStackHeightMm=2400.0,
        axleLoadLimits=AxleLimits(frontKg=4000.0, rearKg=6500.0),
    ),
    Trailer(
        trailerId="T-COOL-004",
        name="Refrigerated Trailer 13.6m",
        lengthMm=13400.0,
        widthMm=2350.0,
        heightMm=2550.0,
        maxWeightKg=22000.0,
        maxStackHeightMm=2550.0,
        axleLoadLimits=AxleLimits(frontKg=7000.0, rearKg=11000.0),
    ),
]

TRAILER_MAP: Dict[str, Trailer] = {t.trailerId: t for t in AVAILABLE_TRAILERS}

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class OptimizeRequest(BaseModel):
    trailerId: str
    products: List[Product]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "TrackLoadSim API"}


@app.get("/api/trailers", response_model=List[Trailer])
def get_trailers() -> List[Trailer]:
    """Return all available trailer definitions."""
    return AVAILABLE_TRAILERS


@app.get("/api/scenarios")
def get_scenarios() -> List[Dict[str, str]]:
    """Return list of available demo scenario names and descriptions."""
    return list_scenarios()


@app.post("/api/optimize", response_model=LoadingPlan)
def optimize(request: OptimizeRequest) -> LoadingPlan:
    """Run the 3D bin packing optimizer for a given trailer and product list."""
    trailer = TRAILER_MAP.get(request.trailerId)
    if trailer is None:
        raise HTTPException(
            status_code=404,
            detail=f"Trailer '{request.trailerId}' not found. "
                   f"Available IDs: {list(TRAILER_MAP.keys())}",
        )

    if not request.products:
        raise HTTPException(status_code=400, detail="Product list must not be empty.")

    plan = packer.pack(trailer, request.products)
    return plan


@app.get("/api/scenarios/{name}/optimize", response_model=LoadingPlan)
def optimize_scenario(name: str) -> LoadingPlan:
    """Fetch a predefined demo scenario and run the optimizer."""
    try:
        scenario = get_scenario(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    plan = packer.pack(scenario["trailer"], scenario["products"])
    return plan


@app.post("/api/import/excel")
async def import_excel(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Import products from an Excel (.xlsx) file.

    Expected columns (case-insensitive):
    productId, name, lengthMm, widthMm, heightMm, weightKg,
    quantity, fragile, compressible, maxStackWeightKg, canRotate,
    stackingGroup, loadingPriority
    """
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be an Excel file (.xlsx or .xls).")

    contents = await file.read()

    try:
        import openpyxl  # type: ignore

        wb = openpyxl.load_workbook(io.BytesIO(contents), read_only=True, data_only=True)
        ws = wb.active

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            raise HTTPException(status_code=400, detail="Excel file is empty.")

        header = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]

        def _col(name: str) -> int:
            try:
                return header.index(name.lower())
            except ValueError:
                return -1

        products: List[Product] = []
        errors: List[str] = []

        for row_idx, row in enumerate(rows[1:], start=2):
            if all(cell is None for cell in row):
                continue

            def _val(col_name: str, default: Any = None) -> Any:
                idx = _col(col_name)
                if idx == -1 or idx >= len(row):
                    return default
                cell = row[idx]
                return cell if cell is not None else default

            try:
                product = Product(
                    productId=str(_val("productId", str(uuid.uuid4()))),
                    name=str(_val("name", f"Product_{row_idx}")),
                    lengthMm=float(_val("lengthMm", 300.0)),
                    widthMm=float(_val("widthMm", 300.0)),
                    heightMm=float(_val("heightMm", 300.0)),
                    weightKg=float(_val("weightKg", 1.0)),
                    quantity=int(_val("quantity", 1)),
                    fragile=bool(_val("fragile", False)),
                    compressible=bool(_val("compressible", False)),
                    maxStackWeightKg=float(_val("maxStackWeightKg", 100.0)),
                    canRotate=bool(_val("canRotate", True)),
                    stackingGroup=str(_val("stackingGroup", "general")),
                    loadingPriority=int(_val("loadingPriority", 5)),
                )
                products.append(product)
            except (ValueError, TypeError) as exc:
                errors.append(f"Row {row_idx}: {exc}")

        return {
            "importedCount": len(products),
            "errors": errors,
            "products": [p.model_dump() for p in products],
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse Excel file: {exc}",
        ) from exc
