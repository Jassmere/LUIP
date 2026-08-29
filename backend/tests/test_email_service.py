import pytest

from email.message import EmailMessage

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings

from app.db.base import Base

from app.models.company import Company
from app.models.decision_maker import DecisionMaker
from app.models.next_best_action import NextBestAction
from app.models.outreach_campaign import OutreachCampaign
from app.models.email_queue import EmailQueue

from app.services.email_service import EmailService


# =========================================================
# LIVE EMAIL TEST AUTHORIZATION
# =========================================================
#
# This test module exercises the SMTP/live execution path.
# The dedicated test_email_live_safety.py module separately
# verifies that the production safety gate blocks live email
# unless explicitly authorized.
#
# These tests NEVER connect to a real SMTP server.
# SMTP execution is monkeypatched where required.
#
# =========================================================

@pytest.fixture(autouse=True)
def authorize_live_email_tests(monkeypatch):

    monkeypatch.setattr(
        EmailService,
        "is_live_enabled",
        staticmethod(
            lambda: True
        ),
    )


# =========================================================
# TEST DATABASE
# =========================================================

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# =========================================================
# DATABASE FIXTURE
# =========================================================

@pytest.fixture(
    scope="function",
    autouse=True,
)
def initialize_test_database():

    Base.metadata.create_all(
        bind=engine
    )

    yield

    Base.metadata.drop_all(
        bind=engine
    )


@pytest.fixture
def db():

    session = TestingSessionLocal()

    try:

        yield session

    finally:

        session.rollback()
        session.close()


# =========================================================
# COMPANY FIXTURE
# =========================================================

@pytest.fixture
def company(
    db,
):

    company = Company(
        name="LUIP Email Service Test Company",
        website="https://example.com",
        industry="Legal Technology",
        country="India",
        city="Mumbai",
        active=True,
    )

    db.add(company)

    db.commit()

    db.refresh(
        company
    )

    return company


# =========================================================
# DECISION MAKER FIXTURE
# =========================================================

@pytest.fixture
def decision_maker(
    db,
    company,
):

    decision_maker = DecisionMaker(
        company_id=company.id,
        full_name="Email Test Decision Maker",
        title="General Counsel",
        department="Legal",
        email="email-test@example.com",
        phone="+910000000000",
        seniority="Executive",
        source="Test",
        verified=True,
    )

    db.add(
        decision_maker
    )

    db.commit()

    db.refresh(
        decision_maker
    )

    return decision_maker


# =========================================================
# NBA FIXTURE
# =========================================================

@pytest.fixture
def nba(
    db,
    company,
):

    nba = NextBestAction(
        company_id=company.id,
        action_type="Call immediately",
        priority="Critical",
        recommended_within_hours=1,
        explanation="Immediate buying intent detected.",
        ai_reasoning="High-intent buying signal detected.",
        status="Pending",
    )

    db.add(nba)

    db.commit()

    db.refresh(nba)

    return nba


# =========================================================
# CAMPAIGN FIXTURE
# =========================================================

@pytest.fixture
def campaign(
    db,
    company,
    decision_maker,
):

    campaign = OutreachCampaign(
        company_id=company.id,
        decision_maker_id=decision_maker.id,
        campaign_name="Email Service Test Campaign",
        campaign_type="Email",
        subject="Test Subject",
        message="Test email body.",
        status="Draft",
    )

    db.add(campaign)

    db.commit()

    db.refresh(campaign)

    return campaign


# =========================================================
# EMAIL QUEUE FIXTURE
# =========================================================

@pytest.fixture
def email_queue(
    db,
    company,
    decision_maker,
    campaign,
):

    queue = EmailQueue(
        company_id=company.id,
        decision_maker_id=decision_maker.id,
        campaign_id=campaign.id,
        recipient_email=decision_maker.email,
        recipient_name=decision_maker.full_name,
        subject="Test Subject",
        body="Test email body.",
        priority="Critical",
        status="Pending",
        retry_count=0,
        max_retries=5,
    )

    db.add(queue)

    db.commit()

    db.refresh(queue)

    return queue


# =========================================================
# VERSION
# =========================================================

def test_email_service_version():

    assert EmailService.VERSION == "1.1.0"


# =========================================================
# SMTP CONFIGURATION
# =========================================================

def test_is_configured_returns_false_when_missing_configuration(
    monkeypatch,
):

    monkeypatch.setattr(
        settings,
        "SMTP_HOST",
        "",
        raising=False,
    )

    monkeypatch.setattr(
        settings,
        "SMTP_PORT",
        587,
        raising=False,
    )

    monkeypatch.setattr(
        settings,
        "SMTP_USERNAME",
        "test-user",
        raising=False,
    )

    monkeypatch.setattr(
        settings,
        "SMTP_PASSWORD",
        "test-password",
        raising=False,
    )

    monkeypatch.setattr(
        settings,
        "SMTP_FROM_EMAIL",
        "sender@example.com",
        raising=False,
    )

    assert (
        EmailService.is_configured()
        is False
    )


def test_is_configured_returns_true_when_configuration_exists(
    monkeypatch,
):

    monkeypatch.setattr(
        settings,
        "SMTP_HOST",
        "smtp.example.com",
        raising=False,
    )

    monkeypatch.setattr(
        settings,
        "SMTP_PORT",
        587,
        raising=False,
    )

    monkeypatch.setattr(
        settings,
        "SMTP_USERNAME",
        "test-user",
        raising=False,
    )

    monkeypatch.setattr(
        settings,
        "SMTP_PASSWORD",
        "test-password",
        raising=False,
    )

    monkeypatch.setattr(
        settings,
        "SMTP_FROM_EMAIL",
        "sender@example.com",
        raising=False,
    )

    assert (
        EmailService.is_configured()
        is True
    )


# =========================================================
# DRY RUN
# =========================================================

def test_is_dry_run_defaults_to_true(
    monkeypatch,
):

    monkeypatch.setattr(
        settings,
        "EMAIL_DRY_RUN",
        True,
        raising=False,
    )

    assert (
        EmailService.is_dry_run()
        is True
    )


def test_is_dry_run_can_be_disabled(
    monkeypatch,
):

    monkeypatch.setattr(
        settings,
        "EMAIL_DRY_RUN",
        False,
        raising=False,
    )

    assert (
        EmailService.is_dry_run()
        is False
    )


# =========================================================
# BUILD EMAIL MESSAGE
# =========================================================

def test_build_email_message(
    email_queue,
    monkeypatch,
):

    monkeypatch.setattr(
        settings,
        "SMTP_FROM_NAME",
        "Lawyered Up",
        raising=False,
    )

    monkeypatch.setattr(
        settings,
        "SMTP_FROM_EMAIL",
        "sender@lawyeredapp.com",
        raising=False,
    )

    message = (
        EmailService.build_email_message(
            email_queue
        )
    )

    assert isinstance(
        message,
        EmailMessage,
    )

    assert (
        message["To"]
        == "email-test@example.com"
    )

    assert (
        message["Subject"]
        == "Test Subject"
    )

    assert (
        message["From"]
        == "Lawyered Up <sender@lawyeredapp.com>"
    )

    assert (
        message.get_content()
        == "Test email body.\n"
    )


# =========================================================
# SEND EMAIL - MISSING RECIPIENT
# =========================================================

def test_send_email_requires_recipient():

    class DummyQueue:

        recipient_email = None

    result = (
        EmailService.send_email(
            DummyQueue()
        )
    )

    assert result["success"] is False

    assert (
        result["error"]
        == "Recipient email address is missing."
    )


# =========================================================
# SEND EMAIL - DRY RUN
# =========================================================

def test_send_email_dry_run(
    email_queue,
    monkeypatch,
):

    monkeypatch.setattr(
        EmailService,
        "is_dry_run",
        staticmethod(
            lambda: True
        ),
    )

    result = (
        EmailService.send_email(
            email_queue
        )
    )

    assert result["success"] is True

    assert result["dry_run"] is True

    assert (
        "skipped"
        in result["message"].lower()
    )


# =========================================================
# SEND EMAIL - SMTP NOT CONFIGURED
# =========================================================

def test_send_email_smtp_not_configured(
    email_queue,
    monkeypatch,
):

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
            lambda: False
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "is_live_enabled",
        staticmethod(
            lambda: True
        ),
    )

    result = (
        EmailService.send_email(
            email_queue
        )
    )

    assert result["success"] is False

    assert (
        result["error"]
        == "SMTP is not configured."
    )


# =========================================================
# FAKE SMTP SERVER
# =========================================================

class FakeSMTP:

    def __init__(self):

        self.sent_messages = []

        self.quit_called = False

    def send_message(
        self,
        message,
    ):

        self.sent_messages.append(
            message
        )

    def quit(self):

        self.quit_called = True


# =========================================================
# SEND EMAIL - LIVE SUCCESS
# =========================================================

def test_send_email_live_success(
    email_queue,
    monkeypatch,
):

    fake_smtp = FakeSMTP()

    monkeypatch.setattr(
        EmailService,
        "is_dry_run",
        staticmethod(
            lambda: False
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "is_live_enabled",
        staticmethod(
            lambda: True
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
        "create_smtp_connection",
        staticmethod(
            lambda: fake_smtp
        ),
    )

    monkeypatch.setattr(
        settings,
        "SMTP_FROM_NAME",
        "Lawyered Up",
        raising=False,
    )

    monkeypatch.setattr(
        settings,
        "SMTP_FROM_EMAIL",
        "sender@example.com",
        raising=False,
    )

    result = (
        EmailService.send_email(
            email_queue
        )
    )

    assert result["success"] is True

    assert result["dry_run"] is False

    assert (
        result["recipient"]
        == "email-test@example.com"
    )

    assert len(
        fake_smtp.sent_messages
    ) == 1

    sent_message = (
        fake_smtp.sent_messages[0]
    )

    assert (
        sent_message["To"]
        == "email-test@example.com"
    )

    assert (
        sent_message["Subject"]
        == "Test Subject"
    )

    assert (
        sent_message.get_content()
        == "Test email body.\n"
    )

    assert (
        fake_smtp.quit_called
        is True
    )


# =========================================================
# SEND EMAIL - SMTP FAILURE
# =========================================================

def test_send_email_smtp_failure(
    email_queue,
    monkeypatch,
):

    monkeypatch.setattr(
        EmailService,
        "is_dry_run",
        staticmethod(
            lambda: False
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "is_live_enabled",
        staticmethod(
            lambda: True
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "is_configured",
        staticmethod(
            lambda: True
        ),
    )

    def failing_connection():

        raise RuntimeError(
            "SMTP connection failed."
        )

    monkeypatch.setattr(
        EmailService,
        "create_smtp_connection",
        staticmethod(
            failing_connection
        ),
    )

    result = (
        EmailService.send_email(
            email_queue
        )
    )

    assert result["success"] is False

    assert (
        result["error"]
        == "SMTP connection failed."
    )


# =========================================================
# PROCESS QUEUE ENTRY - DRY RUN
# =========================================================

def test_process_queue_entry_dry_run(
    db,
    email_queue,
    monkeypatch,
):

    monkeypatch.setattr(
        EmailService,
        "is_dry_run",
        staticmethod(
            lambda: True
        ),
    )

    result = (
        EmailService.process_queue_entry(
            db=db,
            email_queue=email_queue,
        )
    )

    assert result["success"] is True

    assert result["processed"] is True

    assert result["dry_run"] is True

    assert (
        result["queue_id"]
        == email_queue.id
    )

    db.refresh(email_queue)

    assert (
        email_queue.status
        == "Pending"
    )

    assert (
        email_queue.sent_at
        is None
    )


# =========================================================
# PROCESS QUEUE ENTRY - LIVE SUCCESS
# =========================================================

def test_process_queue_entry_live_success(
    db,
    email_queue,
    monkeypatch,
):

    monkeypatch.setattr(
        EmailService,
        "is_dry_run",
        staticmethod(
            lambda: False
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "is_live_enabled",
        staticmethod(
            lambda: True
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "send_email",
        staticmethod(
            lambda queue: {
                "success": True,
                "dry_run": False,
                "message": (
                    "Email sent successfully."
                ),
            }
        ),
    )

    result = (
        EmailService.process_queue_entry(
            db=db,
            email_queue=email_queue,
        )
    )

    assert result["success"] is True

    assert result["processed"] is True

    assert result["dry_run"] is False

    assert (
        result["queue_id"]
        == email_queue.id
    )

    db.refresh(email_queue)

    assert (
        email_queue.status
        == "Sent"
    )

    assert (
        email_queue.sent_at
        is not None
    )

    assert (
        email_queue.error_message
        is None
    )


# =========================================================
# PROCESS QUEUE ENTRY - FAILURE
# =========================================================

def test_process_queue_entry_failure(
    db,
    email_queue,
    monkeypatch,
):

    monkeypatch.setattr(
        EmailService,
        "is_dry_run",
        staticmethod(
            lambda: False
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "is_live_enabled",
        staticmethod(
            lambda: True
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "send_email",
        staticmethod(
            lambda queue: {
                "success": False,
                "error": (
                    "SMTP connection failed."
                ),
            }
        ),
    )

    result = (
        EmailService.process_queue_entry(
            db=db,
            email_queue=email_queue,
        )
    )

    assert result["success"] is False

    assert result["processed"] is True

    assert (
        result["queue_id"]
        == email_queue.id
    )

    assert (
        result["retry_count"]
        == 1
    )

    assert (
        result["max_retries"]
        == 5
    )

    db.refresh(email_queue)

    assert (
        email_queue.status
        == "Failed"
    )

    assert (
        email_queue.retry_count
        == 1
    )

    assert (
        email_queue.error_message
        == "SMTP connection failed."
    )


# =========================================================
# PROCESS QUEUE ENTRY - INVALID STATUS
# =========================================================

def test_process_queue_entry_invalid_status(
    db,
    email_queue,
):

    email_queue.status = "Sent"

    db.commit()
    db.refresh(email_queue)

    result = (
        EmailService.process_queue_entry(
            db=db,
            email_queue=email_queue,
        )
    )

    assert result["success"] is False

    assert result["processed"] is False

    assert (
        "not executable"
        in result["reason"]
    )


# =========================================================
# PROCESS QUEUE ENTRY - MAX RETRIES
# =========================================================

def test_process_queue_entry_max_retries(
    db,
    email_queue,
):

    email_queue.status = "Failed"

    email_queue.retry_count = 5

    email_queue.max_retries = 5

    db.commit()
    db.refresh(email_queue)

    result = (
        EmailService.process_queue_entry(
            db=db,
            email_queue=email_queue,
        )
    )

    assert result["success"] is False

    assert result["processed"] is False

    assert (
        result["reason"]
        == "Maximum retry count reached."
    )


# =========================================================
# PROCESS PENDING QUEUE - DRY RUN
# =========================================================

def test_process_pending_queue_dry_run(
    db,
    email_queue,
    monkeypatch,
):

    monkeypatch.setattr(
        EmailService,
        "is_dry_run",
        staticmethod(
            lambda: True
        ),
    )

    result = (
        EmailService.process_pending_queue(
            db=db,
            limit=10,
        )
    )

    assert result["success"] is True

    assert (
        result["version"]
        == "1.1.0"
    )

    assert result["dry_run"] is True

    assert result["processed"] == 1

    assert result["sent"] == 0

    assert result["failed"] == 0

    assert result["dry_run_count"] == 1

    assert len(
        result["results"]
    ) == 1


# =========================================================
# PROCESS PENDING QUEUE - LIMIT
# =========================================================

def test_process_pending_queue_respects_limit(
    db,
    company,
    decision_maker,
    monkeypatch,
):

    monkeypatch.setattr(
        EmailService,
        "is_dry_run",
        staticmethod(
            lambda: True
        ),
    )

    campaigns = []

    queues = []

    for index in range(3):

        campaign = OutreachCampaign(
            company_id=company.id,
            decision_maker_id=decision_maker.id,
            campaign_name=(
                f"Limit Test Campaign {index}"
            ),
            campaign_type="Email",
            subject=(
                f"Limit Subject {index}"
            ),
            message=(
                f"Limit Body {index}"
            ),
            status="Draft",
        )

        db.add(campaign)

        db.flush()

        campaigns.append(campaign)

        queue = EmailQueue(
            company_id=company.id,
            decision_maker_id=decision_maker.id,
            campaign_id=campaign.id,
            recipient_email=(
                f"recipient{index}@example.com"
            ),
            recipient_name=(
                f"Recipient {index}"
            ),
            subject=(
                f"Limit Subject {index}"
            ),
            body=(
                f"Limit Body {index}"
            ),
            priority="Normal",
            status="Pending",
            retry_count=0,
            max_retries=5,
        )

        db.add(queue)

        queues.append(queue)

    db.commit()

    result = (
        EmailService.process_pending_queue(
            db=db,
            limit=2,
        )
    )

    assert result["success"] is True

    assert result["processed"] == 2


# =========================================================
# PROCESS PENDING QUEUE - PRIORITY
# =========================================================

def test_process_pending_queue_prioritises_critical(
    db,
    company,
    decision_maker,
    monkeypatch,
):

    monkeypatch.setattr(
        EmailService,
        "is_dry_run",
        staticmethod(
            lambda: True
        ),
    )

    campaigns = []

    priorities = [
        "Normal",
        "Critical",
        "High",
    ]

    for index, priority in enumerate(
        priorities
    ):

        campaign = OutreachCampaign(
            company_id=company.id,
            decision_maker_id=decision_maker.id,
            campaign_name=(
                f"Priority Campaign {index}"
            ),
            campaign_type="Email",
            subject=(
                f"Priority Subject {index}"
            ),
            message=(
                f"Priority Body {index}"
            ),
            status="Draft",
        )

        db.add(campaign)

        db.flush()

        queue = EmailQueue(
            company_id=company.id,
            decision_maker_id=decision_maker.id,
            campaign_id=campaign.id,
            recipient_email=(
                f"priority{index}@example.com"
            ),
            recipient_name=(
                f"Priority Recipient {index}"
            ),
            subject=(
                f"Priority Subject {index}"
            ),
            body=(
                f"Priority Body {index}"
            ),
            priority=priority,
            status="Pending",
            retry_count=0,
            max_retries=5,
        )

        db.add(queue)

        campaigns.append(campaign)

    db.commit()

    processed_ids = []

    def fake_process(
        db,
        email_queue,
    ):

        processed_ids.append(
            email_queue.priority
        )

        return {
            "success": True,
            "processed": True,
            "dry_run": True,
            "queue_id": email_queue.id,
        }

    monkeypatch.setattr(
        EmailService,
        "process_queue_entry",
        staticmethod(
            fake_process
        ),
    )

    result = (
        EmailService.process_pending_queue(
            db=db,
            limit=3,
        )
    )

    assert result["success"] is True

    assert result["processed"] == 3

    assert processed_ids == [
        "Critical",
        "High",
        "Normal",
    ]

    assert (
        result["dry_run_count"]
        == 3
    )
