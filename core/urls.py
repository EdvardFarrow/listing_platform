from django.contrib import admin
from django.urls import path, include

from .api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("", include("django_prometheus.urls")),
]
