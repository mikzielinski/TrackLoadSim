from typing import List, Optional
from pydantic import BaseModel


class PlacedItem(BaseModel):
    productId: str
    name: str
    xMm: float
    yMm: float
    zMm: float
    lengthMm: float
    widthMm: float
    heightMm: float
    orientation: str
    weightKg: float
    fragile: bool = False
    stackingGroup: str = "general"
    maxStackWeightKg: float = 100.0


class CenterOfGravity(BaseModel):
    xMm: float
    yMm: float
    zMm: float


class LoadingMetrics(BaseModel):
    volumeUtilizationPct: float
    weightUtilizationPct: float
    frontAxleLoadKg: float
    rearAxleLoadKg: float
    centerOfGravity: CenterOfGravity
    stabilityScore: float
    warnings: List[str]


class LoadingPlan(BaseModel):
    planId: str
    trailerId: str
    items: List[PlacedItem]
    metrics: LoadingMetrics
    loadingSequence: List[str]
    totalWeightKg: float
    placedCount: int
    totalCount: int
