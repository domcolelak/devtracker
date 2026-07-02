from django.contrib import admin

from .models import ExternalTask, TeamProductivityStats


@admin.register(TeamProductivityStats)
class TeamProductivityStatsAdmin(admin.ModelAdmin):
    list_display = ("team", "computed_at", "tasks_total", "tasks_done", "completion_rate")
    list_filter = ("team",)
    ordering = ("-computed_at",)

    def has_add_permission(self, request) -> bool:
        # SNAPSHOTS ARE ONLY EVER WRITTEN BY THE recalculate_productivity_stats CELERY TASK
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False


@admin.register(ExternalTask)
class ExternalTaskAdmin(admin.ModelAdmin):
    """READ-ONLY VIEW INTO api-fastapi's `tasks` TABLE, FOR VISIBILITY IN THE
    DJANGO ADMIN. NEVER EDITABLE HERE - api-fastapi IS THE ONLY WRITER."""

    list_display = ("title", "project", "status", "priority", "assignee", "due_date")
    list_filter = ("status", "priority", "project__team")
    search_fields = ("title",)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
