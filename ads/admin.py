from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from .models import Category


class CategoryAdmin(TreeAdmin):
    form = movenodeform_factory(Category)
    list_display = ["name", "slug"]
    list_display_links = ["name"]

admin.site.register(Category, CategoryAdmin)



    
