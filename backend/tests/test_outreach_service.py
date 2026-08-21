import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base

# =========================================================
# LOAD APPLICATION MODELS
# =========================================================
#
# Importing app.database registers all SQLAlchemy models
# with the shared Base registry before SQLAlchemy attempts
# to configure relationships.
#
from app import database  # noqa: F401


from app.models.company import Company
from app.models.decision_maker import DecisionMaker
from app.models.next_best_action import NextBestAction
from app.models.outreach_campaign import OutreachCampaign
from app.models.email_queue import EmailQueue

from app.services.outreach_service import OutreachService


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
def company(db):

    company = Company(
        name="LUIP Outreach Test Company",
        website="https://example.com",
        industry="Legal Technology",
        country="India",
        city="Mumbai",
        active=True,
    )

    db.add(company)
    db.commit()
    db.refresh(company)

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
        full_name="Test Decision Maker",
        title="General Counsel",
        department="Legal",
        email="decisionmaker@example.com",
        phone="+910000000000",
        seniority="Executive",
        source="Test",
        verified=True,
    )

    db.add(decision_maker)
    db.commit()
    db.refresh(decision_maker)

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
        explanation=(
            "Immediate buying intent detected."
        ),
        ai_reasoning=(
            "LBIT classified the company as "
            "high-intent."
        ),
        status="Pending",
    )

    db.add(nba)
    db.commit()
    db.refresh(nba)

    return nba


# =========================================================
# CREATE OUTREACH
# =========================================================

def test_create_outreach(
    db,
    company,
    decision_maker,
    nba,
):

    result = OutreachService.create_outreach(
        db=db,
        company_id=company.id,
        decision_maker_id=decision_maker.id,
    )

    assert result["success"] is True

    assert result["duplicate"] is False

    assert (
        result["company"]["id"]
        == company.id
    )

    assert (
        result["decision_maker"]["id"]
        == decision_maker.id
    )

    assert (
        result["decision_maker"]["email"]
        == "decisionmaker@example.com"
    )

    assert (
        result["next_best_action"]["id"]
        == nba.id
    )

    assert (
        result["campaign"]["id"]
        is not None
    )

    assert (
        result["campaign"]["status"]
        == "Draft"
    )

    assert (
        result["email_queue"]["status"]
        == "Pending"
    )


# =========================================================
# VERIFY DATABASE RECORDS
# =========================================================

def test_outreach_creates_campaign_and_email_queue(
    db,
    company,
    decision_maker,
    nba,
):

    result = OutreachService.create_outreach(
        db=db,
        company_id=company.id,
        decision_maker_id=decision_maker.id,
    )

    assert result["success"] is True

    campaign = (
        db.query(OutreachCampaign)
        .filter(
            OutreachCampaign.company_id
            == company.id
        )
        .first()
    )

    assert campaign is not None

    assert (
        campaign.decision_maker_id
        == decision_maker.id
    )

    assert campaign.status == "Draft"

    queue = (
        db.query(EmailQueue)
        .filter(
            EmailQueue.company_id
            == company.id
        )
        .first()
    )

    assert queue is not None

    assert (
        queue.decision_maker_id
        == decision_maker.id
    )

    assert (
        queue.campaign_id
        == campaign.id
    )

    assert (
        queue.recipient_email
        == decision_maker.email
    )

    assert queue.status == "Pending"


# =========================================================
# PERSONALISED CONTENT
# =========================================================

def test_outreach_contains_personalised_content(
    db,
    company,
    decision_maker,
    nba,
):

    result = OutreachService.create_outreach(
        db=db,
        company_id=company.id,
        decision_maker_id=decision_maker.id,
    )

    assert result["success"] is True

    subject = (
        result["campaign"]["subject"]
    )

    message = (
        result["campaign"]["message"]
    )

    assert company.name in subject

    assert company.name in message

    assert (
        decision_maker.full_name
        in message
    )

    assert (
        nba.action_type
        in message
    )

    assert (
        nba.priority
        in message
    )


# =========================================================
# AUTOMATIC DECISION MAKER SELECTION
# =========================================================

def test_outreach_selects_decision_maker_automatically(
    db,
    company,
    decision_maker,
    nba,
):

    result = OutreachService.create_outreach(
        db=db,
        company_id=company.id,
    )

    assert result["success"] is True

    assert (
        result["decision_maker"]["id"]
        == decision_maker.id
    )


# =========================================================
# COMPANY NOT FOUND
# =========================================================

def test_outreach_company_not_found(
    db,
):

    result = OutreachService.create_outreach(
        db=db,
        company_id=999999,
    )

    assert result["success"] is False

    assert (
        "not found"
        in result["error"].lower()
    )


# =========================================================
# NO DECISION MAKER
# =========================================================

def test_outreach_requires_decision_maker(
    db,
    company,
    nba,
):

    result = OutreachService.create_outreach(
        db=db,
        company_id=company.id,
    )

    assert result["success"] is False

    assert (
        "decision maker"
        in result["error"].lower()
    )


# =========================================================
# NO NBA
# =========================================================

def test_outreach_requires_pending_nba(
    db,
    company,
    decision_maker,
):

    result = OutreachService.create_outreach(
        db=db,
        company_id=company.id,
        decision_maker_id=decision_maker.id,
    )

    assert result["success"] is False

    assert (
        "next best action"
        in result["error"].lower()
    )


# =========================================================
# NO EMAIL
# =========================================================

def test_outreach_requires_email(
    db,
    company,
    nba,
):

    decision_maker = DecisionMaker(
        company_id=company.id,
        full_name="No Email Contact",
        title="General Counsel",
        department="Legal",
        email=None,
        verified=False,
    )

    db.add(decision_maker)
    db.commit()

    result = OutreachService.create_outreach(
        db=db,
        company_id=company.id,
        decision_maker_id=decision_maker.id,
    )

    assert result["success"] is False

    assert (
        "email"
        in result["error"].lower()
    )


# =========================================================
# DUPLICATE PROTECTION
# =========================================================

def test_outreach_prevents_duplicate_pending_campaign(
    db,
    company,
    decision_maker,
    nba,
):

    first = OutreachService.create_outreach(
        db=db,
        company_id=company.id,
        decision_maker_id=decision_maker.id,
    )

    assert first["success"] is True

    second = OutreachService.create_outreach(
        db=db,
        company_id=company.id,
        decision_maker_id=decision_maker.id,
    )

    assert second["success"] is True

    assert second["duplicate"] is True

    campaigns = (
        db.query(OutreachCampaign)
        .filter(
            OutreachCampaign.company_id
            == company.id,
            OutreachCampaign.decision_maker_id
            == decision_maker.id,
        )
        .all()
    )

    assert len(campaigns) == 1

    queues = (
        db.query(EmailQueue)
        .filter(
            EmailQueue.company_id
            == company.id,
            EmailQueue.decision_maker_id
            == decision_maker.id,
        )
        .all()
    )

    assert len(queues) == 1