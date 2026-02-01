from ninja import Router
from typing import List
from django.shortcuts import get_object_or_404
from .models import Ad, Category
from .schemas import AdOut, AdCreate


router = Router()

# Список объявлений
@router.get("/", response=List[AdOut])
async def list_ads(request):
    qs = Ad.objects.select_related('category', 'seller').filter(status=Ad.Status.ACTIVE)
    
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