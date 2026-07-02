from fastapi import FastAPI

from app.core.config import get_settings
from app.routers import notifications, tasks

settings = get_settings()

app = FastAPI(
    title="DevTracker API",
    description="Public REST and WebSocket API for tasks and real-time notifications.",
    version="0.1.0",
)

app.include_router(tasks.router)
app.include_router(notifications.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """USED BY docker-compose HEALTHCHECK AND THE NGINX UPSTREAM CHECK."""
    return {"status": "ok", "service": "api-fastapi"}
