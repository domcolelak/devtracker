from django.conf import settings
from django.db import models

from apps.projects.models import Project
from apps.teams.models import Team


class ExternalTask(models.Model):
    """
    UNMANAGED READ-ONLY MIRROR OF THE `tasks` TABLE THAT api-fastapi OWNS AND
    MIGRATES VIA ALEMBIC. managed = False MEANS DJANGO NEVER CREATES, ALTERS
    OR DROPS THIS TABLE - IT ONLY LETS CELERY TASKS IN THIS SERVICE QUERY IT
    WITH THE ORM INSTEAD OF RAW SQL. SEE docs/architecture.md.
    """

    id = models.IntegerField(primary_key=True)
    project = models.ForeignKey(
        Project, on_delete=models.DO_NOTHING, db_column="project_id", related_name="+"
    )
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20)
    priority = models.CharField(max_length=20)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        db_column="assignee_id",
        null=True,
        related_name="+",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        db_column="created_by_id",
        related_name="+",
    )
    due_date = models.DateField(null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "tasks"

    def __str__(self) -> str:
        return self.title


class TeamProductivityStats(models.Model):
    """OWNED BY core-django. A NEW SNAPSHOT ROW IS APPENDED PERIODICALLY BY THE
    recalculate_productivity_stats CELERY BEAT TASK (SEE apps/analytics/tasks.py)."""

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="productivity_stats")
    computed_at = models.DateTimeField(auto_now_add=True)
    tasks_total = models.PositiveIntegerField(default=0)
    tasks_done = models.PositiveIntegerField(default=0)
    completion_rate = models.FloatField(default=0.0)

    class Meta:
        ordering = ["-computed_at"]
        verbose_name_plural = "team productivity stats"

    def __str__(self) -> str:
        return f"{self.team.name} @ {self.computed_at:%Y-%m-%d %H:%M} ({self.completion_rate:.0%})"
