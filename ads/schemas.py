from typing import Any, Dict, List, Optional

from ninja import ModelSchema, Schema

from .models import Ad, Category


class CategoryOut(ModelSchema):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon"]


class UserOut(Schema):
    id: int
    username: str


# WRITE
class AdCreate(Schema):
    title: str
    description: str
    price: float
    currency: str = "TJS"
    city: str
    category_id: int
    attributes: Dict[str, Any] = {}
    lat: Optional[float] = None
    lon: Optional[float] = None


# READ
class AdOut(ModelSchema):
    category: CategoryOut
    seller: UserOut
    attributes: Dict[str, Any] = {}
    lat: Optional[float] = None
    lon: Optional[float] = None

    class Meta:
        model = Ad
        fields = [
            "id",
            "title",
            "description",
            "price",
            "currency",
            "city",
            "status",
            "created_at",
            "attributes",
        ]
        
    @staticmethod
    def resolve_lat(obj):
        return obj.location.y if obj.location else None

    @staticmethod
    def resolve_lon(obj):
        return obj.location.x if obj.location else None


class CategoryTree(Schema):
    id: int
    name: str
    slug: str
    icon: str
    children: List['CategoryTree'] = []

CategoryTree.model_rebuild()