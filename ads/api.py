from ninja import Router, Query
from typing import List, Optional
from django.shortcuts import get_object_or_404
from django.contrib.postgres.search import TrigramSimilarity
from .models import Ad, Category
from .schemas import AdOut, AdCreate
from .filters import AdFilter


router = Router()

# Список объявлений
@router.get("/", response=List[AdOut])
async def list_ads(
    request, 
    filters: AdFilter = Query(...), 
    q: Optional[str] = None
):
    qs = Ad.objects.select_related('category', 'seller').filter(status=Ad.Status.ACTIVE)
    
    qs = filters.filter(qs)
    
    if q:
        qs = qs.annotate(
            similarity=TrigramSimilarity('title', q) + TrigramSimilarity('description', q)
        ).filter(
            similarity__gt=0.1
        ).order_by('-similarity') 
    else:
        qs = qs.order_by('-created_at')

    results = []
    async for ad in qs:
        results.append(ad)
        
    return results


# Детали объявления
@router.get("/{ad_id}", response=AdOut)
async def get_ad(request, ad_id: int):
    ad = await Ad.objects.select_related('category', 'seller').aget(id=ad_id)
    return ad


# Создание
# FIXME: Хардкод для MVP. В будущем заменить на JWT auth
@router.post("/", response=AdOut)
async def create_ad(request, payload: AdCreate):
    from users.models import User
    user = await User.objects.afirst()
    
    if not user:
        user = await User.objects.acreate(username="test_user")

    ad = await Ad.objects.acreate(
        seller=user,
        **payload.dict()
    )
    return await Ad.objects.select_related('category', 'seller').aget(id=ad.id)