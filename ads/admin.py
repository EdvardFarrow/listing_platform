from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from .models import Ad, Category


class CategoryAdmin(TreeAdmin):
    form = movenodeform_factory(Category)
    list_display = ["name", "slug"]
    list_display_links = ["name"]

admin.site.register(Category, CategoryAdmin)


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "price", "currency", "status", "seller", "created_at"]
    
    list_filter = ["status", "currency", "created_at", "category"]
    
    search_fields = ["title", "description"]
    
    readonly_fields = ["created_at", "updated_at"]
    
