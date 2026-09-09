from app.scheduler import outreach_scheduler
from app.scheduler.outreach_scheduler import run_outreach
from app.services.email_service import EmailService
from app.models.email_queue import EmailQueue
from app.models.outreach_campaign import OutreachCampaign


# =========================================================
# HELPERS
# =========================================================


class FakeQuery:

    def __init__(self, count_value):
        self.count_value = count_value

    def filter(self, *conditions):
        return self

    def count(self):
        return self.count_value


class FakeSession:

    def __init__(
        self,
        pending_count=0,
        draft_campaign_count=0,
    ):
        self.pending_count = pending_count
        self.draft_campaign_count = draft_campaign_count
        self.closed = False

    def query(self, model):

        if model is EmailQueue:
            return FakeQuery(
                self.pending_count
            )

        if model is OutreachCampaign:
            return FakeQuery(
                self.draft_campaign_count
            )

        raise AssertionError(
            f"Unexpected model queried: {model}"
        )

    def close(self):
        self.closed = True


# =========================================================
# SUCCESS
# =========================================================


def test_run_outreach_success(
    monkeypatch,
):

    fake_db = FakeSession(
        pending_count=5,
        draft_campaign_count=2,
    )

    monkeypatch.setattr(
        outreach_scheduler,
        "SessionLocal",
        lambda: fake_db,
    )

    result = run_outreach()

    assert result["success"] is True
    assert result["automatic_send"] is False
    assert result["manual_send_required"] is True
    assert result["processed"] == 0
    assert result["sent"] == 0
    assert result["failed"] == 0
    assert result["dry_run_count"] == 0
    assert result["pending_count"] == 5
    assert result["draft_campaign_count"] == 2
    assert fake_db.closed is True


# =========================================================
# AUTOMATIC TRANSMISSION DISABLED
# =========================================================


def test_run_outreach_never_processes_email_queue(
    monkeypatch,
):

    fake_db = FakeSession(
        pending_count=10,
        draft_campaign_count=3,
    )

    monkeypatch.setattr(
        outreach_scheduler,
        "SessionLocal",
        lambda: fake_db,
    )

    def fail_if_called(
        *args,
        **kwargs,
    ):

        raise AssertionError(
            "process_pending_queue() must not be called."
        )

    monkeypatch.setattr(
        EmailService,
        "process_pending_queue",
        staticmethod(
            fail_if_called
        ),
    )

    result = run_outreach()

    assert result["success"] is True
    assert result["automatic_send"] is False
    assert result["manual_send_required"] is True
    assert result["pending_count"] == 10
    assert result["draft_campaign_count"] == 3


# =========================================================
# MANUAL SEND REQUIRED
# =========================================================


def test_run_outreach_requires_manual_send(
    monkeypatch,
):

    fake_db = FakeSession(
        pending_count=4,
        draft_campaign_count=1,
    )

    monkeypatch.setattr(
        outreach_scheduler,
        "SessionLocal",
        lambda: fake_db,
    )

    result = run_outreach()

    assert result["success"] is True
    assert result["automatic_send"] is False
    assert result["manual_send_required"] is True
    assert result["sent"] == 0


# =========================================================
# PENDING EMAIL COUNT
# =========================================================


def test_run_outreach_reports_pending_email_count(
    monkeypatch,
):

    fake_db = FakeSession(
        pending_count=17,
        draft_campaign_count=0,
    )

    monkeypatch.setattr(
        outreach_scheduler,
        "SessionLocal",
        lambda: fake_db,
    )

    result = run_outreach()

    assert result["success"] is True
    assert result["pending_count"] == 17
    assert result["processed"] == 0
    assert result["sent"] == 0


# =========================================================
# DRAFT CAMPAIGN COUNT
# =========================================================


def test_run_outreach_reports_draft_campaign_count(
    monkeypatch,
):

    fake_db = FakeSession(
        pending_count=0,
        draft_campaign_count=9,
    )

    monkeypatch.setattr(
        outreach_scheduler,
        "SessionLocal",
        lambda: fake_db,
    )

    result = run_outreach()

    assert result["success"] is True
    assert result["draft_campaign_count"] == 9
    assert result["sent"] == 0


# =========================================================
# ZERO QUEUE / ZERO CAMPAIGNS
# =========================================================


def test_run_outreach_with_no_pending_work(
    monkeypatch,
):

    fake_db = FakeSession(
        pending_count=0,
        draft_campaign_count=0,
    )

    monkeypatch.setattr(
        outreach_scheduler,
        "SessionLocal",
        lambda: fake_db,
    )

    result = run_outreach()

    assert result["success"] is True
    assert result["automatic_send"] is False
    assert result["manual_send_required"] is True
    assert result["processed"] == 0
    assert result["sent"] == 0
    assert result["failed"] == 0
    assert result["dry_run_count"] == 0
    assert result["pending_count"] == 0
    assert result["draft_campaign_count"] == 0


# =========================================================
# SESSION CLOSED ON SUCCESS
# =========================================================


def test_run_outreach_closes_database_session_on_success(
    monkeypatch,
):

    fake_db = FakeSession(
        pending_count=3,
        draft_campaign_count=2,
    )

    monkeypatch.setattr(
        outreach_scheduler,
        "SessionLocal",
        lambda: fake_db,
    )

    result = run_outreach()

    assert result["success"] is True
    assert fake_db.closed is True


# =========================================================
# EXCEPTION HANDLING
# =========================================================


def test_run_outreach_handles_execution_exception(
    monkeypatch,
):

    fake_db = FakeSession()

    def failing_query(model):

        raise RuntimeError(
            "Test scheduler failure."
        )

    fake_db.query = failing_query

    monkeypatch.setattr(
        outreach_scheduler,
        "SessionLocal",
        lambda: fake_db,
    )

    result = run_outreach()

    assert result["success"] is False
    assert result["automatic_send"] is False
    assert result["manual_send_required"] is True
    assert result["processed"] == 0
    assert result["sent"] == 0
    assert result["failed"] == 0
    assert result["dry_run_count"] == 0
    assert result["pending_count"] == 0
    assert result["draft_campaign_count"] == 0
    assert result["error"] == "Test scheduler failure."
    assert fake_db.closed is True


# =========================================================
# SESSION CLOSED ON EXCEPTION
# =========================================================


def test_run_outreach_closes_database_session_on_exception(
    monkeypatch,
):

    fake_db = FakeSession()

    def failing_query(model):

        raise RuntimeError(
            "Database failure."
        )

    fake_db.query = failing_query

    monkeypatch.setattr(
        outreach_scheduler,
        "SessionLocal",
        lambda: fake_db,
    )

    result = run_outreach()

    assert result["success"] is False
    assert result["error"] == "Database failure."
    assert fake_db.closed is True


# =========================================================
# RESULT CONTRACT
# =========================================================


def test_run_outreach_result_contract(
    monkeypatch,
):

    fake_db = FakeSession(
        pending_count=6,
        draft_campaign_count=4,
    )

    monkeypatch.setattr(
        outreach_scheduler,
        "SessionLocal",
        lambda: fake_db,
    )

    result = run_outreach()

    expected_keys = {
        "success",
        "automatic_send",
        "manual_send_required",
        "processed",
        "sent",
        "failed",
        "dry_run_count",
        "pending_count",
        "draft_campaign_count",
    }

    assert set(result.keys()) == expected_keys
    assert result["success"] is True
    assert result["automatic_send"] is False
    assert result["manual_send_required"] is True
    assert result["processed"] == 0
    assert result["sent"] == 0
    assert result["failed"] == 0
    assert result["dry_run_count"] == 0
    assert result["pending_count"] == 6
    assert result["draft_campaign_count"] == 4


# =========================================================
# EMAIL CONFIGURATION NOT REQUIRED
# =========================================================


def test_run_outreach_does_not_require_email_configuration(
    monkeypatch,
):

    fake_db = FakeSession(
        pending_count=8,
        draft_campaign_count=5,
    )

    monkeypatch.setattr(
        outreach_scheduler,
        "SessionLocal",
        lambda: fake_db,
    )

    def fail_dry_run():

        raise AssertionError(
            "is_dry_run() should not be called."
        )

    def fail_configured():

        raise AssertionError(
            "is_configured() should not be called."
        )

    monkeypatch.setattr(
        EmailService,
        "is_dry_run",
        staticmethod(
            fail_dry_run
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "is_configured",
        staticmethod(
            fail_configured
        ),
    )

    result = run_outreach()

    assert result["success"] is True
    assert result["automatic_send"] is False
    assert result["manual_send_required"] is True
    assert result["pending_count"] == 8
    assert result["draft_campaign_count"] == 5