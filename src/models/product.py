from pydantic import BaseModel, Field
from typing import Optional

class Product(BaseModel):
    id: str
    title: str
    price: float
    url: str
    affiliate_url: str
    category: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None 