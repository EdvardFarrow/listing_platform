from ninja import ModelSchema, Schema
from typing import List, Optional
from datetime import datetime
from pydantic import Field
from .models import Ad, Category


# Схема для Категории (вывод)
class CategorySchema(ModelSchema):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon']


# Схема для Автора объявления
class UserSchema(Schema):
    id: int
    username: str
    avatar: Optional[str] = None


# Основная схема Объявления (чтение)
class AdOut(ModelSchema):
    category: CategorySchema
    seller: UserSchema
    image_url: Optional[str] = None
    
    class Meta:
        model = Ad
        fields = ['id', 'title', 'price', 'currency', 'city', 'status', 'created_at']


# Схема для создания Объявления (входные данные)
class AdCreate(Schema):
    title: str
    description: str
    price: float
    currency: str = 'TJS'
    city: str
    category_id: int