from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.common.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "job_title", "is_staff", "is_active")
    search_fields = ("username", "email", "job_title")
    fieldsets = (
        *(DjangoUserAdmin.fieldsets or ()),
        ("DevTracker profile", {"fields": ("job_title", "avatar_url")}),
    )
