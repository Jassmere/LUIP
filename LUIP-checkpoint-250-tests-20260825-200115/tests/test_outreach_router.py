import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base

from app.models.company import Company
from app.models.decision_maker import DecisionMaker
from app.models.next_best_action import NextBestAction
from app.models.outreach_campaign import OutreachCampaign
from app.models.email_queue import EmailQueue

from app.routers.outreach import (
    prepare_outreach,
    list_campaigns,
    get_campaign,
    list_queue,
    update_campaign_status,
    update_queue_status,
    update_campaign_engagement,
    update_queue_engagement,
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
def company(db):

    company = Company(
        name="LUIP Outreach Router Test Company",
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
        full_name="Router Test Decision Maker",
        title="General Counsel",
        department="Legal",
        email="router-test@example.com",
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
        explanation="Immediate buying intent detected.",
        ai_reasoning="High-intent buying signal detected.",
        status="Pending",
    )

    db.add(nba)
    db.commit()
    db.refresh(nba)

    return nba


# =========================================================
# PREPARE OUTREACH
# =========================================================

def test_prepare_outreach(
    db,
    company,
    decision_maker,
    nba,
):

    result = prepare_outreach(
        company_id=company.id,
        decision_maker_id=decision_maker.id,
        campaign_name="Router Test Campaign",
        db=db,
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
        result["next_best_action"]["id"]
        == nba.id
    )

    assert (
        result["campaign"]["name"]
        == "Router Test Campaign"
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
# LIST CAMPAIGNS
# =========================================================

def test_list_campaigns(
    db,
    company,
    decision_maker,
    nba,
):

    prepare_outreach(
        company_id=company.id,
        decision_maker_id=decision_maker.id,
        db=db,
    )

    result = list_campaigns(
        company_id=company.id,
        status=None,
        db=db,
    )

    assert result["success"] is True

    assert result["count"] == 1

    assert len(
        result["campaigns"]
    ) == 1

    assert (
        result["campaigns"][0]["company_id"]
        == company.id
    )

    assert (
        result["campaigns"][0]["status"]
        == "Draft"
    )


# =========================================================
# LIST CAMPAIGNS BY STATUS
# =========================================================

def test_list_campaigns_by_status(
    db,
    company,
    decision_maker,
    nba,
):

    prepare_outreach(
        company_id=company.id,
        decision_maker_id=decision_maker.id,
        db=db,
    )

    result = list_campaigns(
        company_id=company.id,
        status="Draft",
        db=db,
    )

    assert result["success"] is True

    assert result["count"] == 1

    result = list_campaigns(
        company_id=company.id,
        status="Sent",
        db=db,
    )

    assert result["success"] is True

    assert result["count"] == 0


# =========================================================
# GET CAMPAIGN
# =========================================================

def test_get_campaign(
    db,
    company,
    decision_maker,
    nba,
):

    result = prepare_outreach(
        company_id=company.id,
        decision_maker_id=decision_maker.id,
        db=db,
    )

    campaign_id = (
        result["campaign"]["id"]
    )

    result = get_campaign(
        campaign_id=campaign_id,
        db=db,
    )

    assert result["success"] is True

    assert (
        result["campaign"]["id"]
        == campaign_id
    )

    assert (
        result["email_queue"]
        is not None
    )

    assert (
        result["email_queue"]["campaign_id"]
        == campaign_id
    )


# =========================================================
# GET CAMPAIGN NOT FOUND
# =========================================================

def test_get_campaign_not_found(
    db,
):

    with pytest.raises(Exception) as exc_info:

        get_campaign(
            campaign_id=999999,
            db=db,
        )

    assert (
        exc_info.value.status_code
        == 404
    )


# =========================================================
# LIST QUEUE
# =========================================================

def test_list_queue(
    db,
    company,
    decision_maker,
    nba,
):

    prepare_outreach(
        company_id=company.id,
        decision_maker_id=decision_maker.id,
        db=db,
    )

    result = list_queue(
        company_id=company.id,
        campaign_id=None,
        status=None,
        db=db,
    )

    assert result["success"] is True

    assert result["count"] == 1

    assert len(
        result["queue"]
    ) == 1

    assert (
        result["queue"][0]["company_id"]
        == company.id
    )

    assert (
        result["queue"][0]["status"]
        == "Pending"
    )


# =========================================================
# UPDATE CAMPAIGN STATUS
# =========================================================

def test_update_campaign_status(
    db,
    company,
    decision_maker,
    nba,
):

    result = prepare_outreach(
        company_id=company.id,
        decision_maker_id=decision_maker.id,
        db=db,
    )

    campaign_id = (
        result["campaign"]["id"]
    )

    result = update_campaign_status(
        campaign_id=campaign_id,
        status="Scheduled",
        db=db,
    )

    assert result["success"] is True

    assert (
        result["campaign"]["status"]
        == "Scheduled"
    )

    result = update_campaign_status(
        campaign_id=campaign_id,
        status="Sent",
        db=db,
    )

    assert result["success"] is True

    assert (
        result["campaign"]["status"]
        == "Sent"
    )

    assert (
        result["campaign"]["sent_at"]
        is not None
    )


# =========================================================
# UPDATE QUEUE STATUS
# =========================================================

def test_update_queue_status(
    db,
    company,
    decision_maker,
    nba,
):

    result = prepare_outreach(
        company_id=company.id,
        decision_maker_id=decision_maker.id,
        db=db,
    )

    queue_id = (
        result["email_queue"]["id"]
    )

    result = update_queue_status(
        queue_id=queue_id,
        status="Processing",
        error_message=None,
        db=db,
    )

    assert result["success"] is True

    assert (
        result["queue"]["status"]
        == "Processing"
    )

    result = update_queue_status(
        queue_id=queue_id,
        status="Sent",
        error_message=None,
        db=db,
    )

    assert result["success"] is True

    assert (
        result["queue"]["status"]
        == "Sent"
    )

    assert (
        result["queue"]["sent_at"]
        is not None
    )


# =========================================================
# FAILED QUEUE STATUS
# =========================================================

def test_update_queue_status_failed(
    db,
    company,
    decision_maker,
    nba,
):

    result = prepare_outreach(
        company_id=company.id,
        decision_maker_id=decision_maker.id,
        db=db,
    )

    queue_id = (
        result["email_queue"]["id"]
    )

    result = update_queue_status(
        queue_id=queue_id,
        status="Failed",
        error_message="SMTP connection failed.",
        db=db,
    )

    assert result["success"] is True

    assert (
        result["queue"]["status"]
        == "Failed"
    )

    assert (
        result["queue"]["retry_count"]
        == 1
    )

    assert (
        result["queue"]["error_message"]
        == "SMTP connection failed."
    )


# =========================================================
# CAMPAIGN ENGAGEMENT
# =========================================================

def test_update_campaign_engagement(
    db,
    company,
    decision_maker,
    nba,
):

    result = prepare_outreach(
        company_id=company.id,
        decision_maker_id=decision_maker.id,
        db=db,
    )

    campaign_id = (
        result["campaign"]["id"]
    )

    result = update_campaign_engagement(
        campaign_id=campaign_id,
        opened=True,
        clicked=True,
        replied=True,
        meeting_booked=True,
        db=db,
    )

    assert result["success"] is True

    assert (
        result["campaign"]["opened"]
        is True
    )

    assert (
        result["campaign"]["clicked"]
        is True
    )

    assert (
        result["campaign"]["replied"]
        is True
    )

    assert (
        result["campaign"]["meeting_booked"]
        is True
    )


# =========================================================
# QUEUE ENGAGEMENT
# =========================================================

def test_update_queue_engagement(
    db,
    company,
    decision_maker,
    nba,
):

    result = prepare_outreach(
        company_id=company.id,
        decision_maker_id=decision_maker.id,
        db=db,
    )

    queue_id = (
        result["email_queue"]["id"]
    )

    result = update_queue_engagement(
        queue_id=queue_id,
        opened=True,
        clicked=True,
        replied=True,
        bounced=True,
        db=db,
    )

    assert result["success"] is True

    assert (
        result["queue"]["opened"]
        is True
    )

    assert (
        result["queue"]["clicked"]
        is True
    )

    assert (
        result["queue"]["replied"]
        is True
    )

    assert (
        result["queue"]["bounced"]
        is True
    )


# =========================================================
# INVALID CAMPAIGN STATUS
# =========================================================

def test_invalid_campaign_status(
    db,
):

    with pytest.raises(Exception) as exc_info:

        list_campaigns(
            company_id=None,
            status="INVALID",
            db=db,
        )

    assert (
        exc_info.value.status_code
        == 400
    )


# =========================================================
# INVALID QUEUE STATUS
# =========================================================

def test_invalid_queue_status(
    db,
):

    with pytest.raises(Exception) as exc_info:

        list_queue(
            company_id=None,
            campaign_id=None,
            status="INVALID",
            db=db,
        )

    assert (
        exc_info.value.status_code
        == 400
    )


# =========================================================
# CAMPAIGN NOT FOUND
# =========================================================

def test_update_campaign_status_not_found(
    db,
):

    with pytest.raises(Exception) as exc_info:

        update_campaign_status(
            campaign_id=999999,
            status="Sent",
            db=db,
        )

    assert (
        exc_info.value.status_code
        == 404
    )


# =========================================================
# QUEUE NOT FOUND
# =========================================================

def test_update_queue_status_not_found(
    db,
):

    with pytest.raises(Exception) as exc_info:

        update_queue_status(
            queue_id=999999,
            status="Sent",
            error_message=None,
            db=db,
        )

    assert (
        exc_info.value.status_code
        == 404
    )


# =========================================================
# CAMPAIGN ENGAGEMENT NOT FOUND
# =========================================================

def test_update_campaign_engagement_not_found(
    db,
):

    with pytest.raises(Exception) as exc_info:

        update_campaign_engagement(
            campaign_id=999999,
            opened=True,
            clicked=None,
            replied=None,
            meeting_booked=None,
            db=db,
        )

    assert (
        exc_info.value.status_code
        == 404
    )


# =========================================================
# QUEUE ENGAGEMENT NOT FOUND
# =========================================================

def test_update_queue_engagement_not_found(
    db,
):

    with pytest.raises(Exception) as exc_info:

        update_queue_engagement(
            queue_id=999999,
            opened=True,
            clicked=None,
            replied=None,
            bounced=None,
            db=db,
        )

    assert (
        exc_info.value.status_code
        == 404
    )