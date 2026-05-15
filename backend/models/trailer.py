from pydantic import BaseModel


class AxleLimits(BaseModel):
    frontKg: float
    rearKg: float


class Trailer(BaseModel):
    trailerId: str
    name: str
    lengthMm: float
    widthMm: float
    heightMm: float
    maxWeightKg: float
    maxStackHeightMm: float
    axleLoadLimits: AxleLimits
