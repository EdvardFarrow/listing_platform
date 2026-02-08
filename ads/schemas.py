from typing import Any, Dict

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


# READ
class AdOut(ModelSchema):
    category: CategoryOut
    seller: UserOut
    attributes: Dict[str, Any] = {}

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
            "attributes"
        ]
