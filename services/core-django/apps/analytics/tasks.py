import logging

from celery import shared_task
from django.core.mail import send_mail
from django.db.models import Count, Q

from apps.analytics.models import ExternalTask, TeamProductivityStats
from apps.teams.models import Team

logger = logging.getLogger(__name__)


@shared_task
def recalculate_productivity_stats() -> int:
    """RECOMPUTES PER-TEAM TASK COMPLETION STATS FROM api-fastapi's `tasks` TABLE.
    RUN PERIODICALLY BY CELERY BEAT (SEE config/settings.py CELERY_BEAT_SCHEDULE)."""
    teams_processed = 0
    for team in Team.objects.all():
        aggregates = ExternalTask.objects.filter(project__team=team).aggregate(
            total=Count("id"),
            done=Count("id", filter=Q(status="done")),
        )
        total = aggregates["total"] or 0
        done = aggregates["done"] or 0
        completion_rate = (done / total) if total else 0.0

        TeamProductivityStats.objects.create(
            team=team, tasks_total=total, tasks_done=done, completion_rate=completion_rate
        )
        teams_processed += 1

    logger.info("Recalculated productivity stats for %s teams", teams_processed)
    return teams_processed


@shared_task
def send_productivity_email_summary() -> int:
    """SENDS (LOGS, VIA THE console EMAIL_BACKEND) A PRODUCTIVITY SUMMARY TO EACH TEAM'S
    OWNER(S), BASED ON THE MOST RECENT TeamProductivityStats SNAPSHOT. A REAL SMTP
    BACKEND WOULD BE SWAPPED IN VIA EMAIL_BACKEND IN PRODUCTION - THE TASK ITSELF
    DOES NOT CHANGE."""
    emails_sent = 0
    for team in Team.objects.all():
        latest_stats = team.productivity_stats.first()
        if latest_stats is None:
            continue

        owner_emails = [
            membership.user.email
            for membership in team.memberships.filter(role="owner").select_related("user")
            if membership.user.email
        ]
        if not owner_emails:
            continue

        send_mail(
            subject=f"DevTracker productivity summary: {team.name}",
            message=(
                f"{team.name}: {latest_stats.tasks_done}/{latest_stats.tasks_total} tasks done "
                f"({latest_stats.completion_rate:.0%} completion rate) "
                f"as of {latest_stats.computed_at}."
            ),
            from_email=None,
            recipient_list=owner_emails,
        )
        emails_sent += 1

    logger.info("Sent productivity summary email for %s teams", emails_sent)
    return emails_sent
