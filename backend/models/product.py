from typing import List, Optional
from pydantic import BaseModel


class PhysicsProperties(BaseModel):
    friction: float = 0.5
    restitution: float = 0.1


class Product(BaseModel):
    productId: str
    name: str
    lengthMm: float
    widthMm: float
    heightMm: float
    weightKg: float
    quantity: int = 1
    fragile: bool = False
    compressible: bool = False
    maxStackWeightKg: float = 100.0
    canRotate: bool = True
    allowedOrientations: Optional[List[str]] = None
    stackingGroup: str = "general"
    physics: PhysicsProperties = PhysicsProperties()
    loadingPriority: int = 5
