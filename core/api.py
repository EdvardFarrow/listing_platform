from ninja_extra import NinjaExtraAPI 
from ninja_jwt.controller import NinjaJWTDefaultController


api = NinjaExtraAPI() 

api.register_controllers(NinjaJWTDefaultController)

from ads.api import router as ads_router
api.add_router("/ads", ads_router)