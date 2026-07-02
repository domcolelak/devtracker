import pytest
from django.core.management import call_command

from apps.projects.models import Project
from apps.teams.models import Membership, Team

pytestmark = pytest.mark.django_db


def test_seed_creates_expected_objects(django_user_model):
    call_command("seed_demo_data", verbosity=0)

    assert django_user_model.objects.filter(username="admin", is_superuser=True).exists()
    assert django_user_model.objects.filter(username="alice").exists()
    assert Team.objects.count() == 2
    assert Project.objects.count() == 4
    assert Membership.objects.count() == 10


def test_seed_is_idempotent(django_user_model):
    call_command("seed_demo_data", verbosity=0)
    call_command("seed_demo_data", verbosity=0)

    assert django_user_model.objects.filter(username="alice").count() == 1
    assert Team.objects.count() == 2
    assert Project.objects.count() == 4


def test_seeded_user_can_log_in(api_client, django_user_model):
    call_command("seed_demo_data", "--password", "custom-pass-123", verbosity=0)

    response = api_client.post(
        "/auth/token/",
        {"username": "alice", "password": "custom-pass-123"},
        format="json",
    )
    assert response.status_code == 200
