from ninja import FilterSchema, Field
from typing import Optional


class AdFilter(FilterSchema):
    city: Optional[str] = None
    min_price: Optional[float] = Field(None, q='price__gte')
    max_price: Optional[float] = Field(None, q='price__lte')