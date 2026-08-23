import pytest

from app.scheduler import outreach_scheduler
from app.scheduler.outreach_scheduler import run_outreach
from app.services.email_service import EmailService


# =========================================================
# RUN OUTREACH - SUCCESS
# =========================================================


def test_run_outreach_success(
    monkeypatch,
):

    fake_result = {
        "success": True,
        "version": "1.0.0",
        "dry_run": True,
        "processed": 1,
        "sent": 0,
        "failed": 0,
        "dry_run_count": 1,
        "results": [
            {
                "success": True,
                "processed": True,
                "dry_run": True,
                "queue_id": 1,
            }
        ],
    }

    monkeypatch.setattr(
        EmailService,
        "is_dry_run",
        staticmethod(
            lambda: True
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "is_configured",
        staticmethod(
            lambda: False
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "process_pending_queue",
        staticmethod(
            lambda db, limit: fake_result
        ),
    )

    result = run_outreach()

    assert result == fake_result


# =========================================================
# RUN OUTREACH - LIVE SUCCESS
# =========================================================


def test_run_outreach_live_success(
    monkeypatch,
):

    fake_result = {
        "success": True,
        "version": "1.0.0",
        "dry_run": False,
        "processed": 2,
        "sent": 2,
        "failed": 0,
        "dry_run_count": 0,
        "results": [
            {
                "success": True,
                "processed": True,
                "dry_run": False,
                "queue_id": 1,
            },
            {
                "success": True,
                "processed": True,
                "dry_run": False,
                "queue_id": 2,
            },
        ],
    }

    monkeypatch.setattr(
        EmailService,
        "is_dry_run",
        staticmethod(
            lambda: False
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "is_configured",
        staticmethod(
            lambda: True
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "process_pending_queue",
        staticmethod(
            lambda db, limit: fake_result
        ),
    )

    result = run_outreach()

    assert result["success"] is True

    assert result["processed"] == 2

    assert result["sent"] == 2

    assert result["failed"] == 0

    assert result["dry_run_count"] == 0


# =========================================================
# BATCH SIZE
# =========================================================


def test_run_outreach_uses_configured_batch_size(
    monkeypatch,
):

    captured = {}

    fake_result = {
        "success": True,
        "version": "1.0.0",
        "dry_run": True,
        "processed": 0,
        "sent": 0,
        "failed": 0,
        "dry_run_count": 0,
        "results": [],
    }

    monkeypatch.setattr(
        outreach_scheduler.settings,
        "EMAIL_BATCH_SIZE",
        25,
        raising=False,
    )

    monkeypatch.setattr(
        EmailService,
        "is_dry_run",
        staticmethod(
            lambda: True
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "is_configured",
        staticmethod(
            lambda: False
        ),
    )

    def fake_process_pending_queue(
        db,
        limit,
    ):

        captured["limit"] = limit

        return fake_result

    monkeypatch.setattr(
        EmailService,
        "process_pending_queue",
        staticmethod(
            fake_process_pending_queue
        ),
    )

    result = run_outreach()

    assert result["success"] is True

    assert captured["limit"] == 25


# =========================================================
# DEFAULT BATCH SIZE
# =========================================================


def test_run_outreach_uses_default_batch_size(
    monkeypatch,
):

    captured = {}

    fake_result = {
        "success": True,
        "version": "1.0.0",
        "dry_run": True,
        "processed": 0,
        "sent": 0,
        "failed": 0,
        "dry_run_count": 0,
        "results": [],
    }

    monkeypatch.delattr(
        outreach_scheduler.settings,
        "EMAIL_BATCH_SIZE",
        raising=False,
    )

    monkeypatch.setattr(
        EmailService,
        "is_dry_run",
        staticmethod(
            lambda: True
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "is_configured",
        staticmethod(
            lambda: False
        ),
    )

    def fake_process_pending_queue(
        db,
        limit,
    ):

        captured["limit"] = limit

        return fake_result

    monkeypatch.setattr(
        EmailService,
        "process_pending_queue",
        staticmethod(
            fake_process_pending_queue
        ),
    )

    result = run_outreach()

    assert result["success"] is True

    assert captured["limit"] == 10


# =========================================================
# SCHEDULER EXCEPTION HANDLING
# =========================================================


def test_run_outreach_handles_execution_exception(
    monkeypatch,
):

    monkeypatch.setattr(
        EmailService,
        "is_dry_run",
        staticmethod(
            lambda: True
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "is_configured",
        staticmethod(
            lambda: False
        ),
    )

    def failing_process(
        db,
        limit,
    ):

        raise RuntimeError(
            "Test scheduler failure."
        )

    monkeypatch.setattr(
        EmailService,
        "process_pending_queue",
        staticmethod(
            failing_process
        ),
    )

    result = run_outreach()

    assert result["success"] is False

    assert result["processed"] == 0

    assert result["sent"] == 0

    assert result["failed"] == 0

    assert result["dry_run_count"] == 0

    assert (
        result["error"]
        == "Test scheduler failure."
    )


# =========================================================
# DRY-RUN REPORTING
# =========================================================


def test_run_outreach_reports_dry_run(
    monkeypatch,
):

    fake_result = {
        "success": True,
        "version": "1.0.0",
        "dry_run": True,
        "processed": 3,
        "sent": 0,
        "failed": 0,
        "dry_run_count": 3,
        "results": [
            {
                "success": True,
                "processed": True,
                "dry_run": True,
                "queue_id": 1,
            },
            {
                "success": True,
                "processed": True,
                "dry_run": True,
                "queue_id": 2,
            },
            {
                "success": True,
                "processed": True,
                "dry_run": True,
                "queue_id": 3,
            },
        ],
    }

    monkeypatch.setattr(
        EmailService,
        "is_dry_run",
        staticmethod(
            lambda: True
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "is_configured",
        staticmethod(
            lambda: False
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "process_pending_queue",
        staticmethod(
            lambda db, limit: fake_result
        ),
    )

    result = run_outreach()

    assert result["success"] is True

    assert result["dry_run"] is True

    assert result["processed"] == 3

    assert result["sent"] == 0

    assert result["failed"] == 0

    assert result["dry_run_count"] == 3