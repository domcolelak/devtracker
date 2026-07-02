from django.conf import settings
from django.db import models
from django.utils.text import slugify

from devtracker_shared.constants import MembershipRole


class Team(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="teams_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        # AUTO-DERIVE THE SLUG SO API/ADMIN CONSUMERS DO NOT HAVE TO SUPPLY ONE
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Membership(models.Model):
    ROLE_CHOICES = [(role.value, role.name.title()) for role in MembershipRole]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default=MembershipRole.MEMBER.value
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["team", "user"], name="unique_team_membership"),
        ]
        ordering = ["team_id", "role"]

    def __str__(self) -> str:
        return f"{self.user} @ {self.team} ({self.role})"
