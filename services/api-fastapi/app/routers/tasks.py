from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.redis import TASK_EVENTS_CHANNEL, get_redis_client
from app.core.security import CurrentUser, get_current_user
from app.models.external import projects_table
from app.models.task import Task
from app.schemas.notification import TaskEvent, TaskEventName
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def _get_task_or_404(db: AsyncSession, task_id: int) -> Task:
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


async def _ensure_project_exists(db: AsyncSession, project_id: int) -> None:
    # VALIDATED VIA A DIRECT READ AGAINST core-django's projects_project TABLE IN THE
    # SHARED DATABASE RATHER THAN AN HTTP CALL TO core-django (SEE docs/architecture.md)
    result = await db.execute(select(projects_table.c.id).where(projects_table.c.id == project_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found"
        )


async def _publish_task_event(event: TaskEventName, task: Task) -> None:
    redis = get_redis_client()
    message = TaskEvent(event=event, task=TaskRead.model_validate(task))
    await redis.publish(TASK_EVENTS_CHANNEL, message.model_dump_json())


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    project_id: int | None = Query(default=None),
    task_status: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    _current_user: CurrentUser = Depends(get_current_user),
) -> list[Task]:
    stmt = select(Task)
    if project_id is not None:
        stmt = stmt.where(Task.project_id == project_id)
    if task_status is not None:
        stmt = stmt.where(Task.status == task_status)
    stmt = stmt.order_by(Task.created_at.desc())

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> Task:
    await _ensure_project_exists(db, payload.project_id)

    task = Task(
        **payload.model_dump(exclude={"status", "priority"}),
        status=payload.status.value,
        priority=payload.priority.value,
        created_by_id=current_user.user_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    await _publish_task_event("task.created", task)
    return task


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: CurrentUser = Depends(get_current_user),
) -> Task:
    return await _get_task_or_404(db, task_id)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: CurrentUser = Depends(get_current_user),
) -> Task:
    task = await _get_task_or_404(db, task_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value.value if hasattr(value, "value") else value)

    await db.commit()
    await db.refresh(task)

    await _publish_task_event("task.updated", task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: CurrentUser = Depends(get_current_user),
) -> None:
    task = await _get_task_or_404(db, task_id)
    await _publish_task_event("task.deleted", task)

    await db.delete(task)
    await db.commit()
