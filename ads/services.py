from django.db import transaction

from core.services import schedule_event

from .models import Ad


def create_ad(user, data):
    with transaction.atomic():
        ad = Ad.objects.create(
            seller=user,
            **data
        )

        schedule_event(
            topic="ads_events",
            data={
                "event": "created",
                "ad_id": ad.id,
                "title": ad.title,
                "price": float(ad.price),
                "city": ad.city,
                "attributes": ad.attributes
            }
        )
        return ad
