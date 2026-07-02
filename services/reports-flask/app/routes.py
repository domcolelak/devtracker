import csv
from datetime import date, datetime
from io import StringIO

from flask import Blueprint, Response, jsonify, request
from sqlalchemy import case, func, select

from app.auth import require_auth
from app.db import get_engine, projects_table, tasks_table, teams_table, users_table
from app.reports.productivity import build_productivity_pdf

reports_bp = Blueprint("reports", __name__)


@reports_bp.get("/health")
def health_check():
    """USED BY docker-compose HEALTHCHECK AND THE NGINX UPSTREAM CHECK."""
    return jsonify(status="ok", service="reports-flask")


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


@reports_bp.get("/productivity.pdf")
@require_auth
def productivity_report():
    team_id = request.args.get("team_id", type=int)
    if team_id is None:
        return jsonify(detail="team_id query parameter is required"), 400

    start_date = _parse_date(request.args.get("start_date")) or date(2000, 1, 1)
    end_date = _parse_date(request.args.get("end_date")) or date.today()

    engine = get_engine()
    with engine.connect() as conn:
        team = (
            conn.execute(select(teams_table).where(teams_table.c.id == team_id)).mappings().first()
        )
        if team is None:
            return jsonify(detail=f"Team {team_id} not found"), 404

        project_rows = conn.execute(
            select(
                projects_table.c.id,
                projects_table.c.name,
                func.count(tasks_table.c.id).label("total_tasks"),
                func.sum(case((tasks_table.c.status == "done", 1), else_=0)).label("done_tasks"),
            )
            .select_from(
                projects_table.outerjoin(
                    tasks_table, tasks_table.c.project_id == projects_table.c.id
                )
            )
            .where(projects_table.c.team_id == team_id)
            .group_by(projects_table.c.id, projects_table.c.name)
            .order_by(projects_table.c.name)
        ).all()

        user_rows = conn.execute(
            select(
                users_table.c.username,
                func.count(tasks_table.c.id).label("completed_tasks"),
            )
            .select_from(
                tasks_table.join(users_table, users_table.c.id == tasks_table.c.assignee_id).join(
                    projects_table, projects_table.c.id == tasks_table.c.project_id
                )
            )
            .where(
                projects_table.c.team_id == team_id,
                tasks_table.c.status == "done",
                func.date(tasks_table.c.updated_at) >= start_date,
                func.date(tasks_table.c.updated_at) <= end_date,
            )
            .group_by(users_table.c.username)
            .order_by(users_table.c.username)
        ).all()

    pdf_bytes = build_productivity_pdf(
        team_name=team["name"],
        start_date=start_date,
        end_date=end_date,
        project_rows=project_rows,
        user_rows=user_rows,
    )
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=productivity_{team['slug']}.pdf"},
    )


@reports_bp.get("/tasks.csv")
@require_auth
def tasks_csv_export():
    project_id = request.args.get("project_id", type=int)
    team_id = request.args.get("team_id", type=int)
    if project_id is None and team_id is None:
        return jsonify(detail="project_id or team_id query parameter is required"), 400

    stmt = select(
        tasks_table.c.id,
        tasks_table.c.title,
        tasks_table.c.status,
        tasks_table.c.priority,
        users_table.c.username.label("assignee"),
        projects_table.c.name.label("project"),
        tasks_table.c.due_date,
        tasks_table.c.created_at,
    ).select_from(
        tasks_table.join(projects_table, projects_table.c.id == tasks_table.c.project_id).outerjoin(
            users_table, users_table.c.id == tasks_table.c.assignee_id
        )
    )
    if project_id is not None:
        stmt = stmt.where(tasks_table.c.project_id == project_id)
    if team_id is not None:
        stmt = stmt.where(projects_table.c.team_id == team_id)
    stmt = stmt.order_by(tasks_table.c.created_at)

    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["id", "title", "status", "priority", "assignee", "project", "due_date", "created_at"]
    )
    for row in rows:
        writer.writerow(
            [
                row["id"],
                row["title"],
                row["status"],
                row["priority"],
                row["assignee"] or "",
                row["project"],
                row["due_date"] or "",
                row["created_at"],
            ]
        )

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=tasks_export.csv"},
    )
