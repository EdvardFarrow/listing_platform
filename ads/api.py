from typing import List, Optional

from django.db import transaction
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.contrib.gis.geos import Point
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from core.search import search_vacancies
from core.services import schedule_event

from .models import Category, Company, Vacancy, Resume
from .schemas import (
    VacancyCreate, VacancyOut,
    ResumeCreate, ResumeOut,
    CategoryOut, CategoryTree
)

router = Router()

# =======================
# ВАКАНСИИ
# =======================

@router.get("/vacancies", response=List[VacancyOut])
async def list_vacancies(
    request: HttpRequest,
    q: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius: int = 10,
    offset: int = 0,
    limit: int = 20
):
    found_ids = await search_vacancies(
        query=q, lat=lat, lon=lon, radius_km=radius, limit=limit, offset=offset
    )
    
    if not found_ids:
        return []

    qs = Vacancy.objects.select_related("category", "company").filter(id__in=found_ids)
    
    vacancies_map = {v.id: v async for v in qs}
    sorted_results = [vacancies_map[vid] for vid in found_ids if vid in vacancies_map]

    return sorted_results

@router.get("/vacancies/{vacancy_id}", response=VacancyOut)
async def get_vacancy(request: HttpRequest, vacancy_id: int):
    return await Vacancy.objects.select_related("category", "company").aget(id=vacancy_id)

@router.post("/vacancies", response=VacancyOut, auth=JWTAuth())
def create_vacancy(request: HttpRequest, payload: VacancyCreate):
    with transaction.atomic():
        category = get_object_or_404(Category, id=payload.category_id)
        
        # Заглушка: ищем компанию юзера, если нет - создаем дефолтную
        company, _ = Company.objects.get_or_create(
            owner=request.user,
            defaults={"name": f"Компания пользователя {request.user.username}"}
        )
        
        location = None
        if payload.lat and payload.lon:
            location = Point(payload.lon, payload.lat, srid=4326)

        vacancy = Vacancy.objects.create(
            company=company,
            category=category,
            title=payload.title,
            description=payload.description,
            salary_from=payload.salary_from,
            salary_to=payload.salary_to,
            currency=payload.currency,
            city=payload.city,
            attributes=payload.attributes,
            location=location,
            status=Vacancy.Status.ACTIVE
        )
        
        geo_data = None
        if payload.lat and payload.lon:
            geo_data = {"lat": payload.lat, "lon": payload.lon}

        schedule_event(
            topic="vacancies_events",
            data={
                "event": "created",
                "data": {
                    "vacancy_id": vacancy.id,
                    "title": vacancy.title,
                    "description": vacancy.description,
                    "salary_from": float(vacancy.salary_from) if vacancy.salary_from else None,
                    "salary_to": float(vacancy.salary_to) if vacancy.salary_to else None,
                    "city": vacancy.city,
                    "attributes": vacancy.attributes,
                    "location": geo_data
                }
            }
        )
    return vacancy


# =======================
# КАТЕГОРИИ
# =======================

@router.get("/categories", response=List[CategoryTree])
def list_categories(request):
    tree_data = Category.dump_bulk()
    
    def flatten_category(node):
        data = node.pop('data') 
        node.update(data)
        
        if 'children' in node:
            for child in node['children']:
                flatten_category(child)
        return node

    return [flatten_category(node) for node in tree_data]

@router.get("/categories/{category_id}/breadcrumbs", response=List[CategoryOut])
def get_category_breadcrumbs(request, category_id: int):
    category = get_object_or_404(Category, id=category_id)
    return list(category.get_ancestors()) + [category]