from typing import List, Optional

from django.db import transaction
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from core.search import search_ads
from core.services import schedule_event

from .models import Ad, Category
from .schemas import AdCreate, AdOut

router = Router()


# List of ads
@router.get("/", response=List[AdOut])
async def list_ads(
    request: HttpRequest,
    q: Optional[str] = None,
    offset: int = 0,
    limit: int = 20
):
    found_ids = await search_ads(query=q, limit=limit, offset=offset)

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

        ad = Ad.objects.create(
            seller=request.user,
            category=category,
            title=payload.title,
            description=payload.description,
            price=payload.price,
            currency=payload.currency,
            city=payload.city,
            attributes=payload.attributes,
            status=Ad.Status.ACTIVE
        )

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
                    "attributes": ad.attributes
                }
            }
        )

        ad.refresh_from_db()

    return ad
