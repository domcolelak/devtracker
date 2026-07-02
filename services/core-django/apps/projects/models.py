from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.teams.models import Team


class Project(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="projects_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["team", "slug"], name="unique_project_slug_per_team"),
        ]
        ordering = ["team_id", "name"]

    def __str__(self) -> str:
        return f"{self.team.name} / {self.name}"

    def save(self, *args, **kwargs):
        # AUTO-DERIVE THE SLUG SO API/ADMIN CONSUMERS DO NOT HAVE TO SUPPLY ONE
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
