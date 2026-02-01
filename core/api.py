from ninja import NinjaAPI

from ads.api import router as ads_router

api = NinjaAPI(title="Listing Async API", description="Listing PLatform API")

api.add_router("/ads", ads_router)
