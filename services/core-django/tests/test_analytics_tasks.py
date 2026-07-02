import pytest
from django.core import mail

from apps.analytics.models import TeamProductivityStats
from apps.analytics.tasks import recalculate_productivity_stats, send_productivity_email_summary
from tests.conftest import insert_task

pytestmark = pytest.mark.django_db


class TestRecalculateProductivityStats:
    def test_snapshot_reflects_task_completion(self, tasks_table, team, project, user):
        insert_task(1, project.id, status="done", assignee_id=user.id, created_by_id=user.id)
        insert_task(2, project.id, status="in_progress", assignee_id=user.id, created_by_id=user.id)
        insert_task(3, project.id, status="done", assignee_id=user.id, created_by_id=user.id)

        processed = recalculate_productivity_stats()

        assert processed == 1
        stats = TeamProductivityStats.objects.get(team=team)
        assert stats.tasks_total == 3
        assert stats.tasks_done == 2
        assert stats.completion_rate == pytest.approx(2 / 3)

    def test_team_without_tasks_gets_zero_snapshot(self, tasks_table, team):
        recalculate_productivity_stats()

        stats = TeamProductivityStats.objects.get(team=team)
        assert stats.tasks_total == 0
        assert stats.completion_rate == 0.0

    def test_each_run_appends_a_new_snapshot(self, tasks_table, team):
        recalculate_productivity_stats()
        recalculate_productivity_stats()

        assert TeamProductivityStats.objects.filter(team=team).count() == 2


class TestSendProductivityEmailSummary:
    def test_email_sent_to_team_owner(self, tasks_table, team, project, user):
        insert_task(1, project.id, status="done", assignee_id=user.id, created_by_id=user.id)
        recalculate_productivity_stats()

        sent = send_productivity_email_summary()

        assert sent == 1
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["alice@example.com"]
        assert "Platform" in mail.outbox[0].subject
        assert "1/1" in mail.outbox[0].body

    def test_no_email_without_stats_snapshot(self, tasks_table, team):
        sent = send_productivity_email_summary()

        assert sent == 0
        assert mail.outbox == []
