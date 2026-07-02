from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from apps.projects.models import Project
from apps.teams.models import Membership, Team
from devtracker_shared.constants import MembershipRole

User = get_user_model()

DEMO_USERS = [
    {"username": "alice", "email": "alice@example.com", "job_title": "Engineering Lead"},
    {"username": "bob", "email": "bob@example.com", "job_title": "Backend Engineer"},
    {"username": "carol", "email": "carol@example.com", "job_title": "Frontend Engineer"},
    {"username": "dave", "email": "dave@example.com", "job_title": "Product Manager"},
    {"username": "erin", "email": "erin@example.com", "job_title": "QA Engineer"},
]

DEMO_TEAMS = [
    {"name": "Platform", "description": "Core infrastructure and shared services."},
    {"name": "Growth", "description": "Acquisition, activation and retention experiments."},
]

DEMO_PROJECTS = {
    "Platform": ["DevTracker API", "Internal Tooling"],
    "Growth": ["Onboarding Revamp", "Referral Program"],
}


class Command(BaseCommand):
    help = "Seed the database with demo users, teams, memberships and projects."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--password",
            default="devtracker123",
            help="Password for every demo user, including 'admin' (default: devtracker123).",
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        password = options["password"]

        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin", email="admin@example.com", password=password
            )
            self.stdout.write(self.style.SUCCESS("Created superuser 'admin'"))

        users = {}
        for data in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={"email": data["email"], "job_title": data["job_title"]},
            )
            if created:
                user.set_password(password)
                user.save()
            users[data["username"]] = user

        admin_user = User.objects.get(username="admin")

        for team_data in DEMO_TEAMS:
            team, _ = Team.objects.get_or_create(
                name=team_data["name"],
                defaults={"description": team_data["description"], "created_by": admin_user},
            )

            for index, user in enumerate(users.values()):
                role = MembershipRole.OWNER.value if index == 0 else MembershipRole.MEMBER.value
                Membership.objects.get_or_create(team=team, user=user, defaults={"role": role})

            for project_name in DEMO_PROJECTS.get(team_data["name"], []):
                Project.objects.get_or_create(
                    team=team,
                    name=project_name,
                    defaults={"created_by": admin_user},
                )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
        self.stdout.write(
            f"Demo login: username=<any of alice/bob/carol/dave/erin/admin> password={password}"
        )
