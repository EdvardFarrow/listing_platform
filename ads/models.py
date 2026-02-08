from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.indexes import GinIndex
from treebeard.mp_tree import MP_Node


class Category(MP_Node):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True)


    node_order_by = ['name']

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Ad(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активно"
        SOLD = "sold", "Продано"
        DRAFT = "draft", "Черновик"
        REJECTED = "rejected", "Отклонено"

    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="TJS")

    # JSONB: {"mileage": 150000, "brand": "BMW", "color": "Black"}
    attributes = models.JSONField(default=dict, blank=True)

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ads"
    )
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="ads")

    location = models.PointField(srid=4326, null=True, spatial_index=True)
    city = models.CharField(max_length=50, db_index=True)

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            GinIndex(fields=["attributes"], name="ad_attributes_gin"),
        ]

    def __str__(self) -> str:
        return self.title
