# =========================================================
# LUIP EMAIL LIVE SAFETY TESTS
# =========================================================
#
# This module verifies the production safety gates around
# live email transmission.
#
# IMPORTANT:
#
# These tests do NOT send real email.
#
# They verify that:
#
# 1. Live email is blocked when authorization is disabled.
# 2. The live block occurs before SMTP configuration is used.
# 3. Dry-run mode takes precedence over live authorization.
# 4. process_pending_queue fails closed when live execution
#    is not authorized.
# 5. EMAIL_LIVE_MAX_BATCH limits live queue execution.
#
# The normal EmailService test module exercises the actual
# SMTP/live execution path using monkeypatched SMTP objects.
#
# =========================================================


import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings

from app.db.base import Base

from app.models.company import Company
from app.models.decision_maker import DecisionMaker
from app.models.outreach_campaign import OutreachCampaign
from app.models.email_queue import EmailQueue

from app.services.email_service import EmailService


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
        name="LUIP Live Safety Test Company",
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
        full_name="LUIP Live Safety Decision Maker",
        title="General Counsel",
        department="Legal",
        email="live-safety@example.com",
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
        campaign_name="LUIP Live Safety Campaign",
        campaign_type="Email",
        subject="LUIP Safety Test",
        message="LUIP live safety test email.",
        status="Draft",
    )

    db.add(
        campaign
    )

    db.commit()

    db.refresh(
        campaign
    )

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
        subject="LUIP Safety Test",
        body="LUIP live safety test email.",
        priority="Critical",
        status="Pending",
        retry_count=0,
        max_retries=5,
    )

    db.add(
        queue
    )

    db.commit()

    db.refresh(
        queue
    )

    return queue


# =========================================================
# LIVE SAFETY - SEND EMAIL BLOCKED
# =========================================================

def test_send_email_is_blocked_when_live_email_is_disabled(
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
            lambda: False
        ),
    )

    result = (
        EmailService.send_email(
            email_queue
        )
    )

    assert result["success"] is False

    assert result["live_blocked"] is True

    assert (
        result["provider"]
        == "default"
    )

    assert (
        result["error"]
        == (
            "Live email transmission is disabled. "
            "Set EMAIL_LIVE_ENABLED=True only after "
            "SMTP configuration and pilot approval "
            "have been completed."
        )
    )


# =========================================================
# LIVE SAFETY - BLOCK BEFORE SMTP
# =========================================================

def test_send_email_live_block_occurs_before_smtp_configuration(
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
            lambda: False
        ),
    )

    smtp_configuration_checked = []

    def unexpected_configuration_check():

        smtp_configuration_checked.append(
            True
        )

        raise AssertionError(
            "SMTP configuration must not be checked "
            "when live email is blocked."
        )

    monkeypatch.setattr(
        EmailService,
        "is_configured",
        staticmethod(
            unexpected_configuration_check
        ),
    )

    result = (
        EmailService.send_email(
            email_queue
        )
    )

    assert result["success"] is False

    assert result["live_blocked"] is True

    assert (
        smtp_configuration_checked
        == []
    )


# =========================================================
# LIVE SAFETY - DRY RUN OVERRIDES LIVE AUTHORIZATION
# =========================================================

def test_dry_run_prevents_live_transmission_even_when_live_is_enabled(
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

    monkeypatch.setattr(
        EmailService,
        "is_live_enabled",
        staticmethod(
            lambda: True
        ),
    )

    smtp_connection_attempted = []

    def unexpected_smtp_connection():

        smtp_connection_attempted.append(
            True
        )

        raise AssertionError(
            "SMTP connection must not be created "
            "during dry-run execution."
        )

    monkeypatch.setattr(
        EmailService,
        "create_smtp_connection",
        staticmethod(
            unexpected_smtp_connection
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
        result["provider"]
        == "default"
    )

    assert (
        smtp_connection_attempted
        == []
    )


# =========================================================
# LIVE SAFETY - QUEUE PROCESSING BLOCKED
# =========================================================

def test_process_pending_queue_is_blocked_when_live_email_is_disabled(
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
            lambda: False
        ),
    )

    result = (
        EmailService.process_pending_queue(
            db=db,
            limit=10,
        )
    )

    assert result["success"] is False

    assert (
        result["version"]
        == EmailService.VERSION
    )

    assert result["dry_run"] is False

    assert result["live_blocked"] is True

    assert result["processed"] == 0

    assert result["sent"] == 0

    assert result["failed"] == 0

    assert result["dry_run_count"] == 0

    assert result["stale_recovered"] == 0

    assert result["scheduled_skipped"] == 0

    assert (
        result["results"]
        == []
    )

    assert (
        result["error"]
        == (
            "Live email transmission is disabled. "
            "Set EMAIL_LIVE_ENABLED=True only after "
            "SMTP configuration and pilot approval "
            "have been completed."
        )
    )

    db.refresh(
        email_queue
    )

    assert (
        email_queue.status
        == "Pending"
    )


# =========================================================
# LIVE SAFETY - MAX BATCH CEILING
# =========================================================

def test_process_pending_queue_respects_live_max_batch(
    db,
    company,
    decision_maker,
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

    monkeypatch.setattr(
        settings,
        "EMAIL_LIVE_MAX_BATCH",
        1,
        raising=False,
    )

    queues = []

    for index in range(3):

        campaign = OutreachCampaign(
            company_id=company.id,
            decision_maker_id=decision_maker.id,
            campaign_name=(
                f"Live Safety Batch Campaign {index}"
            ),
            campaign_type="Email",
            subject=(
                f"Live Safety Batch Subject {index}"
            ),
            message=(
                f"Live Safety Batch Body {index}"
            ),
            status="Draft",
        )

        db.add(
            campaign
        )

        db.flush()

        queue = EmailQueue(
            company_id=company.id,
            decision_maker_id=decision_maker.id,
            campaign_id=campaign.id,
            recipient_email=(
                f"batch{index}@example.com"
            ),
            recipient_name=(
                f"Batch Recipient {index}"
            ),
            subject=(
                f"Live Safety Batch Subject {index}"
            ),
            body=(
                f"Live Safety Batch Body {index}"
            ),
            priority="Normal",
            status="Pending",
            retry_count=0,
            max_retries=5,
        )

        db.add(
            queue
        )

        queues.append(
            queue
        )

    db.commit()

    processed_ids = []

    def fake_process(
        db,
        email_queue,
    ):

        processed_ids.append(
            email_queue.id
        )

        return {
            "success": True,
            "processed": True,
            "dry_run": False,
            "queue_id": email_queue.id,
            "message": (
                "Email queue entry sent."
            ),
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
            limit=10,
        )
    )

    assert result["success"] is True

    assert result["dry_run"] is False

    assert result["processed"] == 1

    assert result["sent"] == 1

    assert result["failed"] == 0

    assert result["dry_run_count"] == 0

    assert len(
        result["results"]
    ) == 1

    assert len(
        processed_ids
    ) == 1