from types import SimpleNamespace

from app.config import settings
from app.services.email_service import EmailService


class FakeQuery:
    def __init__(self, entries):
        self.entries = entries

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return self.entries


class FakeDB:
    def __init__(self, entries):
        self.entries = entries

    def query(self, model):
        return FakeQuery(self.entries)


def make_queue(queue_id, priority="Normal"):
    return SimpleNamespace(
        id=queue_id,
        priority=priority,
        created_at=queue_id,
        scheduled_for=None,
        status="Pending",
        retry_count=0,
        max_retries=5,
        updated_at=None,
        sent_at=None,
        error_message=None,
        campaign_id=None,
        recipient_email=f"test{queue_id}@example.com",
        subject="Test",
        body="Test email",
    )


def test_live_mode_respects_live_max_batch(monkeypatch):
    entries = [
        make_queue(1, "Critical"),
        make_queue(2, "High"),
        make_queue(3, "Medium"),
        make_queue(4, "Normal"),
    ]

    db = FakeDB(entries)

    monkeypatch.setattr(
        settings,
        "EMAIL_DRY_RUN",
        False,
    )

    monkeypatch.setattr(
        settings,
        "EMAIL_LIVE_ENABLED",
        True,
    )

    monkeypatch.setattr(
        settings,
        "EMAIL_LIVE_MAX_BATCH",
        1,
    )

    monkeypatch.setattr(
        EmailService,
        "recover_stale_processing",
        staticmethod(lambda db, stale_minutes=30: 0),
    )

    monkeypatch.setattr(
        EmailService,
        "is_scheduled_for_future",
        staticmethod(lambda entry: False),
    )

    processed_ids = []

    def fake_process_queue_entry(db, email_queue):
        processed_ids.append(email_queue.id)

        return {
            "success": True,
            "processed": True,
            "dry_run": False,
            "queue_id": email_queue.id,
        }

    monkeypatch.setattr(
        EmailService,
        "process_queue_entry",
        staticmethod(fake_process_queue_entry),
    )

    result = EmailService.process_pending_queue(
        db=db,
        limit=10,
    )

    assert result["success"] is True
    assert result["processed"] == 1
    assert result["sent"] == 1
    assert result["failed"] == 0
    assert result["dry_run_count"] == 0

    assert processed_ids == [1]


def test_live_mode_uses_lower_of_batch_limit_and_live_max_batch(
    monkeypatch,
):
    entries = [
        make_queue(1, "Critical"),
        make_queue(2, "High"),
        make_queue(3, "Medium"),
    ]

    db = FakeDB(entries)

    monkeypatch.setattr(
        settings,
        "EMAIL_DRY_RUN",
        False,
    )

    monkeypatch.setattr(
        settings,
        "EMAIL_LIVE_ENABLED",
        True,
    )

    monkeypatch.setattr(
        settings,
        "EMAIL_LIVE_MAX_BATCH",
        2,
    )

    monkeypatch.setattr(
        EmailService,
        "recover_stale_processing",
        staticmethod(lambda db, stale_minutes=30: 0),
    )

    monkeypatch.setattr(
        EmailService,
        "is_scheduled_for_future",
        staticmethod(lambda entry: False),
    )

    processed_ids = []

    def fake_process_queue_entry(db, email_queue):
        processed_ids.append(email_queue.id)

        return {
            "success": True,
            "processed": True,
            "dry_run": False,
            "queue_id": email_queue.id,
        }

    monkeypatch.setattr(
        EmailService,
        "process_queue_entry",
        staticmethod(fake_process_queue_entry),
    )

    result = EmailService.process_pending_queue(
        db=db,
        limit=10,
    )

    assert result["success"] is True
    assert result["processed"] == 2
    assert result["sent"] == 2
    assert result["failed"] == 0

    assert processed_ids == [1, 2]


def test_dry_run_does_not_apply_live_max_batch(
    monkeypatch,
):
    entries = [
        make_queue(1, "Critical"),
        make_queue(2, "High"),
        make_queue(3, "Medium"),
    ]

    db = FakeDB(entries)

    monkeypatch.setattr(
        settings,
        "EMAIL_DRY_RUN",
        True,
    )

    monkeypatch.setattr(
        settings,
        "EMAIL_LIVE_ENABLED",
        False,
    )

    monkeypatch.setattr(
        settings,
        "EMAIL_LIVE_MAX_BATCH",
        1,
    )

    monkeypatch.setattr(
        EmailService,
        "recover_stale_processing",
        staticmethod(lambda db, stale_minutes=30: 0),
    )

    monkeypatch.setattr(
        EmailService,
        "is_scheduled_for_future",
        staticmethod(lambda entry: False),
    )

    processed_ids = []

    def fake_process_queue_entry(db, email_queue):
        processed_ids.append(email_queue.id)

        return {
            "success": True,
            "processed": True,
            "dry_run": True,
            "queue_id": email_queue.id,
        }

    monkeypatch.setattr(
        EmailService,
        "process_queue_entry",
        staticmethod(fake_process_queue_entry),
    )

    result = EmailService.process_pending_queue(
        db=db,
        limit=3,
    )

    assert result["success"] is True
    assert result["processed"] == 3
    assert result["sent"] == 0
    assert result["failed"] == 0
    assert result["dry_run_count"] == 3

    assert processed_ids == [1, 2, 3]


def test_live_mode_is_blocked_without_explicit_authorization(
    monkeypatch,
):
    entry = make_queue(1)
    db = FakeDB([entry])

    monkeypatch.setattr(
        settings,
        "EMAIL_DRY_RUN",
        False,
    )

    monkeypatch.setattr(
        settings,
        "EMAIL_LIVE_ENABLED",
        False,
    )

    result = EmailService.process_pending_queue(
        db=db,
        limit=10,
    )

    assert result["success"] is False
    assert result["live_blocked"] is True
    assert result["processed"] == 0
    assert result["sent"] == 0
    assert result["failed"] == 0
    assert result["results"] == []

    assert entry.status == "Pending"
    assert entry.retry_count == 0


def test_process_queue_entry_does_not_change_queue_when_live_blocked(
    monkeypatch,
):
    entry = make_queue(1)
    db = FakeDB([entry])

    monkeypatch.setattr(
        settings,
        "EMAIL_DRY_RUN",
        False,
    )

    monkeypatch.setattr(
        settings,
        "EMAIL_LIVE_ENABLED",
        False,
    )

    result = EmailService.process_queue_entry(
        db=db,
        email_queue=entry,
    )

    assert result["success"] is False
    assert result["processed"] is False
    assert result["live_blocked"] is True

    assert entry.status == "Pending"
    assert entry.retry_count == 0