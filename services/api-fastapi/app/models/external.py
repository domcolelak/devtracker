from sqlalchemy import Column, Integer, String, Table

from app.models.base import Base

# READ-ONLY REFLECTIONS OF TABLES OWNED AND MIGRATED BY core-django.
#
# THESE MUST LIVE IN Base.metadata (THE SAME METADATA AS Task) BECAUSE
# SQLALCHEMY RESOLVES STRING-STYLE ForeignKey TARGETS BY LOOKING THEM UP IN
# THE OWNING TABLE'S METADATA - AND THAT RESOLUTION IS NOT ONLY NEEDED FOR
# DDL, BUT ALSO BY THE ORM UNIT OF WORK ON EVERY INSERT/UPDATE (TO SORT
# TABLES BY FK DEPENDENCY). A SEPARATE MetaData FOR THESE CAUSES
# NoReferencedTableError AT RUNTIME, NOT JUST DURING CREATE TABLE.
#
# THIS DOES NOT MAKE api-fastapi RESPONSIBLE FOR THEIR SCHEMA: THIS SERVICE'S
# ALEMBIC MIGRATIONS ONLY EVER CALL op.create_table("tasks", ...) EXPLICITLY.
# --autogenerate MUST NOT BE USED BLINDLY IN THIS PROJECT; IF IT EVER IS, ANY
# DIFF TOUCHING projects_project/teams_team/common_user MUST BE DELETED
# BEFORE APPLYING, SINCE core-django OWNS AND MIGRATES THOSE TABLES.
projects_table = Table(
    "projects_project",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("team_id", Integer, nullable=False),
    Column("name", String(200), nullable=False),
    Column("slug", String(220), nullable=False),
    Column("status", String(20), nullable=False),
)

teams_table = Table(
    "teams_team",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(150), nullable=False),
    Column("slug", String(170), nullable=False),
)

users_table = Table(
    "common_user",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(150), nullable=False),
    Column("email", String(254), nullable=False),
)
