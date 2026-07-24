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

class Company(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="companies")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="companies/logos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Vacancy(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активно"
        CLOSED = "closed", "Закрыто"
        DRAFT = "draft", "Черновик"

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="vacancies")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="vacancies")
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    salary_from = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_to = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="RUB")

    # Сюда пишем теги: {"skills": ["Python", "FastAPI"], "grade": "Middle", "format": "Remote"}
    attributes = models.JSONField(default=dict, blank=True)

    location = models.PointField(srid=4326, null=True, spatial_index=True)
    city = models.CharField(max_length=50, db_index=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            GinIndex(fields=["attributes"], name="vacancy_attributes_gin"),
        ]

    def __str__(self):
        return self.title

class Resume(models.Model):
    class Status(models.TextChoices):
        PUBLISHED = "published", "Опубликовано"
        HIDDEN = "hidden", "Скрыто"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resumes")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="resumes")
    
    title = models.CharField(max_length=200) # Например: "Senior Backend Developer"
    about = models.TextField()
    
    expected_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="RUB")

    # Сюда складываем скиллы и опыт
    attributes = models.JSONField(default=dict, blank=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.HIDDEN, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [GinIndex(fields=["attributes"], name="resume_attributes_gin")]

class Application(models.Model):
    """Отклики на вакансии"""
    class Status(models.TextChoices):
        NEW = "new", "Новый"
        VIEWED = "viewed", "Просмотрен"
        REJECTED = "rejected", "Отказ"
        OFFER = "offer", "Оффер"

    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name="applications")
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="applications")
    
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("vacancy", "resume") # Один соискатель = один отклик на вакансию