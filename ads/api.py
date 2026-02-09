from typing import List, Optional

from django.db import transaction
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.contrib.gis.geos import Point
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from core.search import search_ads
from core.services import schedule_event

from .models import Ad, Category
from .schemas import AdCreate, AdOut, CategoryOut, CategoryTree



router = Router()


# List of ads
@router.get("/", response=List[AdOut])
async def list_ads(
    request: HttpRequest,
    q: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius: int = 10,
    offset: int = 0,
    limit: int = 20
):
    found_ids = await search_ads(
        query=q, 
        lat=lat, 
        lon=lon, 
        radius_km=radius,
        limit=limit, 
        offset=offset,
    )

    if not found_ids:
        return []

    ads_qs = Ad.objects.select_related("category", "seller").filter(id__in=found_ids)

    ads_list = []
    async for ad in ads_qs:
        ads_list.append(ad)

    ads_map = {ad.id: ad for ad in ads_list}

    sorted_results = [ads_map[aid] for aid in found_ids if aid in ads_map]

    return sorted_results

# Details of ads
@router.get("/{ad_id}", response=AdOut)
async def get_ad(request: HttpRequest, ad_id: int):
    ad = await Ad.objects.select_related("category", "seller").aget(id=ad_id)
    return ad


# Create
@router.post("/", response=AdOut, auth=JWTAuth())
def create_ad(request: HttpRequest, payload: AdCreate):
    with transaction.atomic():
        category = get_object_or_404(Category, id=payload.category_id)
        
        location = None
        if payload.lat and payload.lon:
            location = Point(payload.lon, payload.lat, srid=4326)

        ad = Ad.objects.create(
            seller=request.user,
            category=category,
            title=payload.title,
            description=payload.description,
            price=payload.price,
            currency=payload.currency,
            city=payload.city,
            attributes=payload.attributes,
            location=location,
            status=Ad.Status.ACTIVE
        )
        
        geo_data = None
        if payload.lat and payload.lon:
            geo_data = {"lat": payload.lat, "lon": payload.lon}

        schedule_event(
            topic="ads_events",
            data={
                "event": "created",
                "data": {
                    "ad_id": ad.id,
                    "title": ad.title,
                    "description": ad.description,
                    "price": float(ad.price),
                    "city": ad.city,
                    "attributes": ad.attributes,
                    "location": geo_data
                }
            }
        )

        ad.refresh_from_db()

    return ad


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
    
    ancestors = list(category.get_ancestors())
    
    breadcrumbs = ancestors + [category]
    
    return breadcrumbs