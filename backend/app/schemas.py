from pydantic import BaseModel, Field
from typing import Optional, List

class TalkRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)

class TalkResponse(BaseModel):
    product_id: int
    product_name: str
    answer: str
    sources: List[str] = []
    mode: str

class RecommendationRequest(BaseModel):
    budget: Optional[float] = Field(default=None, ge=0)
    occasion: Optional[str] = None
    material: Optional[str] = None
    category: Optional[str] = None

class ProductOut(BaseModel):
    id: int
    name: str
    category: str
    price: float
    original_price: Optional[float] = None
    material: str
    color: str
    fit: str
    style: str
    occasions: str
    description: str
    care: str
    manufactured_in: Optional[str] = None
    origin_verified: bool
    rating: float
    review_summary: str
    image_emoji: str
    accent: str
    match_score: Optional[int] = None

    class Config:
        from_attributes = True
