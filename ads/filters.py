from typing import Optional

from ninja import Field, FilterSchema


class AdFilter(FilterSchema):
    city: Optional[str] = None
    min_price: Optional[float] = Field(default=None, q="price__gte") # type: ignore
    max_price: Optional[float] = Field(default=None, q="price__lte") # type: ignore
