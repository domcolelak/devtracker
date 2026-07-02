import os

from sqlalchemy import Column, Date, DateTime, Integer, MetaData, String, Table, Text, create_engine
from sqlalchemy.engine import Engine

# reports-flask NEVER MIGRATES ANYTHING - IT ONLY EVER RUNS SELECT QUERIES
# AGAINST TABLES core-django (projects_project, teams_team, common_user) AND
# api-fastapi (tasks) OWN AND MIGRATE. NO ForeignKey OBJECTS ARE DECLARED
# HERE SINCE PLAIN CORE SELECT/JOIN QUERIES DON'T NEED THEM - JOINS ARE
# WRITTEN EXPLICITLY BELOW WITH .join(a, a.c.x == b.c.y).
metadata = MetaData()

teams_table = Table(
    "teams_team",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(150), nullable=False),
    Column("slug", String(170), nullable=False),
)

projects_table = Table(
    "projects_project",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("team_id", Integer, nullable=False),
    Column("name", String(200), nullable=False),
    Column("slug", String(220), nullable=False),
    Column("status", String(20), nullable=False),
)

users_table = Table(
    "common_user",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(150), nullable=False),
    Column("email", String(254), nullable=False),
)

tasks_table = Table(
    "tasks",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("project_id", Integer, nullable=False),
    Column("title", String(200), nullable=False),
    Column("description", Text, nullable=True),
    Column("status", String(20), nullable=False),
    Column("priority", String(20), nullable=False),
    Column("assignee_id", Integer, nullable=True),
    Column("created_by_id", Integer, nullable=False),
    Column("due_date", Date, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        database_url = os.environ.get(
            "DATABASE_URL", "postgresql://devtracker:devtracker@localhost:5432/devtracker"
        )
        # THIS SERVICE SHIPS psycopg (VERSION 3), BUT SQLALCHEMY'S BARE
        # postgresql:// SCHEME DEFAULTS TO THE psycopg2 DRIVER - SPELL THE
        # DRIVER OUT SO THE SHARED DATABASE_URL VALUE WORKS UNCHANGED
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        _engine = create_engine(database_url, pool_pre_ping=True)
    return _engine
