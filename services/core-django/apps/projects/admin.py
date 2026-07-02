from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "team", "status", "created_by", "created_at")
    list_filter = ("status", "team")
    search_fields = ("name", "slug", "team__name")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["team", "created_by"]
