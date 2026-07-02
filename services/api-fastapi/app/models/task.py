from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from devtracker_shared.constants import TaskPriority, TaskStatus


class Task(Base):
    """
    OWNED BY api-fastapi AND MIGRATED VIA ALEMBIC. project_id, assignee_id AND
    created_by_id ARE REAL FOREIGN KEYS INTO TABLES core-django OWNS AND
    MIGRATES (projects_project, common_user). BOTH SERVICES SHARE ONE
    POSTGRESQL INSTANCE BUT EACH SERVICE MIGRATES ONLY ITS OWN TABLES - SEE
    docs/architecture.md FOR THE FULL RATIONALE.

    THE FK COLUMNS BELOW SPELL OUT Integer EXPLICITLY (INSTEAD OF RELYING ON
    Mapped[int] INFERENCE): SINCE THE REFERENCED TABLES LIVE OUTSIDE THIS
    MODULE'S METADATA, SQLALCHEMY CANNOT COPY THEIR COLUMN TYPE AND WOULD
    OTHERWISE FALL BACK TO NullType, WHICH BREAKS DDL GENERATION.
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects_project.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[str] = mapped_column(String(20), default=TaskStatus.TODO.value)
    priority: Mapped[str] = mapped_column(String(20), default=TaskPriority.MEDIUM.value)
    assignee_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("common_user.id", ondelete="SET NULL"), nullable=True
    )
    created_by_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("common_user.id", ondelete="RESTRICT")
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
