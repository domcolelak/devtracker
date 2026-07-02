import pytest
from django.db import IntegrityError

from apps.projects.models import Project
from apps.teams.models import Membership, Team


@pytest.mark.django_db
class TestTeam:
    def test_slug_is_derived_from_name(self, user):
        team = Team.objects.create(name="Data Platform Crew", created_by=user)
        assert team.slug == "data-platform-crew"

    def test_explicit_slug_is_kept(self, user):
        team = Team.objects.create(name="Data Platform Crew", slug="dpc", created_by=user)
        assert team.slug == "dpc"

    def test_str(self, team):
        assert str(team) == "Platform"


@pytest.mark.django_db
class TestMembership:
    def test_same_user_cannot_join_team_twice(self, team, user):
        with pytest.raises(IntegrityError):
            Membership.objects.create(team=team, user=user, role="member")

    def test_default_role_is_member(self, team, django_user_model):
        other = django_user_model.objects.create_user(
            username="bob", email="bob@example.com", password="x"
        )
        membership = Membership.objects.create(team=team, user=other)
        assert membership.role == "member"


@pytest.mark.django_db
class TestProject:
    def test_slug_unique_per_team_not_globally(self, team, user):
        other_team = Team.objects.create(name="Growth", created_by=user)
        Project.objects.create(team=team, name="Website", created_by=user)
        # SAME NAME IN A DIFFERENT TEAM IS FINE
        Project.objects.create(team=other_team, name="Website", created_by=user)
        with pytest.raises(IntegrityError):
            Project.objects.create(team=team, name="Website", created_by=user)

    def test_default_status_is_active(self, project):
        assert project.status == Project.Status.ACTIVE

    def test_str_includes_team(self, project):
        assert str(project) == "Platform / DevTracker API"
