from django.db import models
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    # FK для дерева категорий (Электроника -> Телефоны -> Apple)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, 
        null=True, blank=True, related_name='children'
    )
    icon = models.CharField(max_length=50, blank=True) 

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Ad(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Активно'
        SOLD = 'sold', 'Продано'
        DRAFT = 'draft', 'Черновик'

    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='TJS')
    
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ads')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='ads')
    
    # Индексируем город и статус, так как по ним будут частые фильтры
    city = models.CharField(max_length=50, db_index=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    search_vector = SearchVectorField(null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # Композитный индекс: быстрый поиск активных объявлений, отсортированных по дате
            models.Index(fields=['status', '-created_at']),
            # GIN индекс для поиска ('iphone' -> 'iPhone 17')
            GinIndex(fields=['search_vector']),
        ]

    def __str__(self):
        return self.title

class AdImage(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='ads/')
    is_main = models.BooleanField(default=False)