from collections.abc import Sequence
from datetime import date
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_productivity_pdf(
    *,
    team_name: str,
    start_date: date,
    end_date: date,
    project_rows: Sequence[Any],
    user_rows: Sequence[Any],
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"{team_name} productivity report")
    styles = getSampleStyleSheet()

    story = [
        Paragraph(f"DevTracker productivity report - {team_name}", styles["Title"]),
        Paragraph(f"Period: {start_date.isoformat()} to {end_date.isoformat()}", styles["Normal"]),
        Spacer(1, 1 * cm),
        Paragraph("Projects", styles["Heading2"]),
    ]

    project_data = [["Project", "Total tasks", "Done", "Completion"]]
    for row in project_rows:
        total = row.total_tasks or 0
        done = int(row.done_tasks or 0)
        completion = f"{(done / total * 100):.0f}%" if total else "-"
        project_data.append([row.name, str(total), str(done), completion])
    if len(project_data) == 1:
        project_data.append(["No projects in this team yet", "-", "-", "-"])

    story.append(_styled_table(project_data))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Tasks completed per team member in the period", styles["Heading2"]))

    user_data = [["Team member", "Completed tasks"]]
    for row in user_rows:
        user_data.append([row.username, str(row.completed_tasks)])
    if len(user_data) == 1:
        user_data.append(["No completed tasks in this period", "0"])

    story.append(_styled_table(user_data))

    doc.build(story)
    return buffer.getvalue()


def _styled_table(data: list[list[str]]) -> Table:
    table = Table(data, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table
