from typing import List, Optional
from users.models import User
from django.contrib.postgres.search import TrigramSimilarity
from django.http import HttpRequest
from ninja import Query, Router
from core.event_bus import publish_event
from .filters import AdFilter
from .models import Ad
from .schemas import AdCreate, AdOut
from ninja_jwt.authentication import JWTAuth


router = Router()


# Список объявлений
@router.get("/", response=List[AdOut])
async def list_ads(request: HttpRequest, filters: AdFilter = Query(...), q: Optional[str] = None): # noqa: B008
    qs = Ad.objects.select_related("category", "seller").filter(status=Ad.Status.ACTIVE)

    qs = filters.filter(qs)

    if q:
        qs = (
            qs.annotate(
                similarity=TrigramSimilarity("title", q)
                + TrigramSimilarity("description", q)
            )
            .filter(similarity__gt=0.1)
            .order_by("-similarity")
        )
    else:
        qs = qs.order_by("-created_at")

    results = []
    async for ad in qs:
        results.append(ad)

    return results


# Детали объявления
@router.get("/{ad_id}", response=AdOut)
async def get_ad(request: HttpRequest, ad_id: int):
    ad = await Ad.objects.select_related("category", "seller").aget(id=ad_id)
    return ad


# Создание
@router.post("/", response=AdOut, auth=JWTAuth())
async def create_ad(request: HttpRequest, payload: AdCreate):
    user = request.user 
    
    ad = await Ad.objects.acreate(
        seller=user,
        **payload.dict()
    )
    
    ad_with_relations = await Ad.objects.select_related('category', 'seller').aget(id=ad.id)

    await publish_event(
        topic="ads_events",
        data={
            "event": "created",
            "ad_id": ad_with_relations.id,
            "title": ad_with_relations.title,
            "description": ad_with_relations.description,
            "price": float(ad_with_relations.price),
            "city": ad_with_relations.city,
            "seller_id": user.id
        }
    )
    
    return ad_with_relations