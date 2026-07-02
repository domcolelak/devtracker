from typing import Literal

from pydantic import BaseModel

from app.schemas.task import TaskRead

TaskEventName = Literal["task.created", "task.updated", "task.deleted"]


class TaskEvent(BaseModel):
    """SHAPE OF MESSAGES PUBLISHED ON THE task_events REDIS CHANNEL AND FORWARDED
    VERBATIM TO CONNECTED /ws/notifications CLIENTS."""

    event: TaskEventName
    task: TaskRead
