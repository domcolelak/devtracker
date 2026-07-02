from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """METADATA FOR TABLES api-fastapi OWNS AND MIGRATES VIA ALEMBIC (CURRENTLY JUST `tasks`).
    TABLES OWNED BY core-django ARE DELIBERATELY KEPT OUT OF THIS METADATA - SEE
    app/models/external.py."""
