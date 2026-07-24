from typing import Any, Dict, List, Optional
from ninja import ModelSchema, Schema
from .models import Category, Company, Vacancy, Resume, Application

class CategoryOut(ModelSchema):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon"]

class UserOut(Schema):
    id: int
    username: str

class CompanyOut(ModelSchema):
    class Meta:
        model = Company
        fields = ["id", "name", "description", "logo"]

# --- ВАКАНСИИ ---
class VacancyCreate(Schema):
    category_id: int
    title: str
    description: str
    salary_from: Optional[float] = None
    salary_to: Optional[float] = None
    currency: str = "RUB"
    city: str
    attributes: Dict[str, Any] = {}
    lat: Optional[float] = None
    lon: Optional[float] = None

class VacancyOut(ModelSchema):
    category: CategoryOut
    company: CompanyOut
    attributes: Dict[str, Any] = {}
    lat: Optional[float] = None
    lon: Optional[float] = None

    class Meta:
        model = Vacancy
        fields = [
            "id", "title", "description", "salary_from", "salary_to",
            "currency", "city", "status", "created_at", "attributes",
        ]

    @staticmethod
    def resolve_lat(obj):
        return obj.location.y if obj.location else None

    @staticmethod
    def resolve_lon(obj):
        return obj.location.x if obj.location else None

# --- РЕЗЮМЕ ---
class ResumeCreate(Schema):
    category_id: int
    title: str
    about: str
    expected_salary: Optional[float] = None
    currency: str = "RUB"
    attributes: Dict[str, Any] = {}

class ResumeOut(ModelSchema):
    category: CategoryOut
    user: UserOut
    attributes: Dict[str, Any] = {}

    class Meta:
        model = Resume
        fields = [
            "id", "title", "about", "expected_salary",
            "currency", "status", "created_at", "attributes",
        ]

# --- ДЕРЕВО КАТЕГОРИЙ ---
class CategoryTree(Schema):
    id: int
    name: str
    slug: str
    icon: str
    children: List['CategoryTree'] = []

CategoryTree.model_rebuild()