import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base

# =========================================================
# IMPORT MODELS
# =========================================================

from app.models.company import Company
from app.models.buying_activity import BuyingActivity
from app.models.buying_intent_signal import BuyingIntentSignal
from app.models.company_score import CompanyScore
from app.models.next_best_action import NextBestAction
from app.models.decision_maker import DecisionMaker

# =========================================================
# IMPORT SERVICES
# =========================================================

from app.services.discovery_signal_bridge import (
    DiscoverySignalBridge,
)

from app.services.buying_intelligence_service import (
    BuyingIntelligenceService,
)

from app.services.buying_signal_service import (
    BuyingSignalService,
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
# DATABASE INITIALISATION
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


# =========================================================
# DATABASE FIXTURE
# =========================================================

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

    test_company = Company(
        name=(
            "LUIP Discovery Score NBA "
            "Integration Test Company"
        ),
        website="https://example.com",
        industry="Legal Technology",
        country="India",
        city="Mumbai",
        active=True,
    )

    db.add(test_company)

    db.commit()

    db.refresh(test_company)

    yield test_company


# =========================================================
# DISCOVERY → COMPANY SCORE
# =========================================================

def test_discovery_signal_flows_into_company_score(
    db,
    company,
):
    """
    Verify the first half of the LUIP intelligence
    pipeline:

        Discovery
             ↓
        Buying Signal
             ↓
        Buying Activity
             ↓
        Company Score

    The current Buying Intelligence Service is responsible
    for calculating the company score.

    Next Best Action generation is deliberately tested
    separately because the current Buying Intelligence
    Service does not automatically create an NBA.
    """

    # -----------------------------------------------------
    # STEP 1 — PROCESS DISCOVERY
    # -----------------------------------------------------

    discovery_result = (
        DiscoverySignalBridge.website_signals(
            db=db,
            company=company,
            discovery_result={
                "success": True,
                "title": (
                    "Enterprise Contract "
                    "Management Platform"
                ),
                "description": (
                    "Contract lifecycle management "
                    "and contract automation."
                ),
                "text": (
                    "Our platform helps legal teams "
                    "manage contracts."
                ),
                "final_url": (
                    "https://example.com/contracts"
                ),
            },
        )
    )

    assert (
        discovery_result["success"]
        is True
    )

    assert (
        discovery_result["signals_created"]
        >= 1
    )

    # -----------------------------------------------------
    # STEP 2 — VERIFY DISCOVERY CREATED SIGNAL
    # -----------------------------------------------------

    discovery_signals = (
        db.query(BuyingIntentSignal)
        .filter(
            BuyingIntentSignal.company_id
            == company.id
        )
        .all()
    )

    assert (
        len(discovery_signals)
        >= 1
    )

    # -----------------------------------------------------
    # STEP 3 — VERIFY DISCOVERY CREATED ACTIVITY
    # -----------------------------------------------------

    discovery_activities = (
        db.query(BuyingActivity)
        .filter(
            BuyingActivity.company_id
            == company.id
        )
        .all()
    )

    assert (
        len(discovery_activities)
        >= 1
    )

    # -----------------------------------------------------
    # STEP 4 — CALCULATE COMPANY SCORE
    # -----------------------------------------------------

    company_score = (
        BuyingIntelligenceService.calculate_company_score(
            db=db,
            company_id=company.id,
        )
    )

    assert company_score is not None

    assert (
        company_score.company_id
        == company.id
    )

    assert (
        company_score.buying_intent_score
        > 0
    )

    assert (
        company_score.buying_intent_score
        <= 100
    )

    # -----------------------------------------------------
    # STEP 5 — VERIFY CONFIDENCE
    # -----------------------------------------------------

    assert (
        company_score.confidence
        >= 0
    )

    assert (
        company_score.confidence
        <= 100
    )

    # -----------------------------------------------------
    # STEP 6 — VERIFY PRIORITY
    # -----------------------------------------------------

    assert (
        company_score.priority
        in {
            "Low",
            "Medium",
            "High",
        }
    )


# =========================================================
# DISCOVERY ACTIVITY → COMPANY INTELLIGENCE
# =========================================================

def test_discovery_activity_is_visible_in_company_intelligence(
    db,
    company,
):
    """
    Verify that a discovery-generated buying activity
    becomes visible through the company-level Buying
    Intelligence service.
    """

    # -----------------------------------------------------
    # STEP 1 — PROCESS DISCOVERY
    # -----------------------------------------------------

    result = (
        DiscoverySignalBridge.website_signals(
            db=db,
            company=company,
            discovery_result={
                "success": True,
                "title": (
                    "Contract Management"
                ),
                "description": (
                    "Contract lifecycle management."
                ),
                "text": "",
                "final_url": (
                    "https://example.com/contracts"
                ),
            },
        )
    )

    assert (
        result["success"]
        is True
    )

    assert (
        result["signals_created"]
        >= 1
    )

    # -----------------------------------------------------
    # STEP 2 — CALCULATE COMPANY SCORE
    # -----------------------------------------------------

    score = (
        BuyingIntelligenceService.calculate_company_score(
            db=db,
            company_id=company.id,
        )
    )

    assert score is not None

    # -----------------------------------------------------
    # STEP 3 — GET COMPANY INTELLIGENCE
    # -----------------------------------------------------

    intelligence = (
        BuyingIntelligenceService.get_company(
            company_id=company.id,
            db=db,
        )
    )

    # -----------------------------------------------------
    # STEP 4 — VERIFY COMPANY
    # -----------------------------------------------------

    assert (
        intelligence["company_id"]
        == company.id
    )

    assert (
        intelligence["company"]
        == company.name
    )

    # -----------------------------------------------------
    # STEP 5 — VERIFY SCORE
    # -----------------------------------------------------

    assert (
        intelligence["buying_intent_score"]
        == score.buying_intent_score
    )

    assert (
        intelligence["confidence"]
        == score.confidence
    )

    assert (
        intelligence["priority"]
        == score.priority
    )

    # -----------------------------------------------------
    # STEP 6 — VERIFY ACTIVITIES
    # -----------------------------------------------------

    assert (
        len(intelligence["activities"])
        >= 1
    )


# =========================================================
# DISCOVERY ACTIVITY SCORE CONTRIBUTION
# =========================================================

def test_discovery_activity_contributes_to_company_score(
    db,
    company,
):
    """
    Verify that a discovery-generated buying activity
    contributes directly to the company buying-intent score.
    """

    # -----------------------------------------------------
    # STEP 1 — PROCESS DISCOVERY
    # -----------------------------------------------------

    result = (
        DiscoverySignalBridge.website_signals(
            db=db,
            company=company,
            discovery_result={
                "success": True,
                "title": (
                    "Contract Management"
                ),
                "description": "",
                "text": "",
                "final_url": (
                    "https://example.com/contracts"
                ),
            },
        )
    )

    assert (
        result["success"]
        is True
    )

    assert (
        result["signals_created"]
        == 1
    )

    # -----------------------------------------------------
    # STEP 2 — VERIFY ACTIVITY
    # -----------------------------------------------------

    activities = (
        db.query(BuyingActivity)
        .filter(
            BuyingActivity.company_id
            == company.id
        )
        .all()
    )

    assert (
        len(activities)
        == 1
    )

    activity = activities[0]

    assert (
        activity.buying_score
        == 35.0
    )

    assert (
        activity.confidence
        == 80.0
    )

    # -----------------------------------------------------
    # STEP 3 — CALCULATE COMPANY SCORE
    # -----------------------------------------------------

    score = (
        BuyingIntelligenceService.calculate_company_score(
            db=db,
            company_id=company.id,
        )
    )

    assert score is not None

    assert (
        score.buying_intent_score
        == 35.0
    )

    assert (
        score.confidence
        == 80.0
    )

    assert (
        score.priority
        == "Low"
    )


# =========================================================
# COMPANY SCORE CAP
# =========================================================

def test_company_score_remains_capped_at_100(
    db,
    company,
):
    """
    Verify that multiple buying activities cannot push
    the company-level score above 100.
    """

    # -----------------------------------------------------
    # CREATE MULTIPLE ACTIVITIES
    # -----------------------------------------------------

    for index in range(4):

        activity = BuyingActivity(
            company_id=company.id,
            activity_type=(
                "Integration Test"
            ),
            activity_source=(
                "Integration Test"
            ),
            title=(
                f"High Intent Activity {index}"
            ),
            description=(
                "High-intent test activity."
            ),
            buying_score=40.0,
            confidence=90.0,
            processed=False,
        )

        db.add(activity)

    db.commit()

    # -----------------------------------------------------
    # CALCULATE SCORE
    # -----------------------------------------------------

    score = (
        BuyingIntelligenceService.calculate_company_score(
            db=db,
            company_id=company.id,
        )
    )

    assert score is not None

    assert (
        score.buying_intent_score
        == 100.0
    )

    assert (
        score.buying_intent_score
        <= 100.0
    )

    assert (
        score.priority
        == "High"
    )


# =========================================================
# VERIFIED LBIT → NBA PROPAGATION
# =========================================================

def test_verified_lbit_signal_creates_next_best_action(
    db,
    company,
):
    """
    Verify the already-supported LBIT → NBA pipeline.

        Buying Signal
             ↓
           LBIT
             ↓
       Next Best Action
             ↓
      Explainable Reasoning

    This test intentionally uses the verified Level 5
    "Requested demo" rule.
    """

    result = (
        BuyingSignalService.create_signal(
            db=db,
            company_id=company.id,
            signal_name="Requested demo",
            signal_category=(
                "Direct Buying Intent"
            ),
            source="Integration Test",
            source_url=(
                "https://example.com/demo"
            ),
            evidence=(
                "The company requested a "
                "product demonstration."
            ),
            score=95,
            confidence=95,
        )
    )

    # -----------------------------------------------------
    # VERIFY SIGNAL
    # -----------------------------------------------------

    assert (
        result["success"]
        is True
    )

    # -----------------------------------------------------
    # VERIFY LBIT
    # -----------------------------------------------------

    assert (
        result["lbit"]["classified"]
        is True
    )

    assert (
        result["lbit"]["level"]
        is not None
    )

    assert (
        result["lbit"]["category"]
        is not None
    )

    assert (
        result["lbit"]["score"]
        is not None
    )

    assert (
        result["lbit"]["confidence"]
        is not None
    )

    # -----------------------------------------------------
    # VERIFY NBA
    # -----------------------------------------------------

    nba = (
        db.query(NextBestAction)
        .filter(
            NextBestAction.company_id
            == company.id
        )
        .filter(
            NextBestAction.status
            == "Pending"
        )
        .order_by(
            NextBestAction.created_at.desc()
        )
        .first()
    )

    assert nba is not None

    assert (
        nba.priority
        == "Critical"
    )

    assert (
        nba.action_type
        == "Call immediately"
    )

    # -----------------------------------------------------
    # VERIFY AI REASONING
    # -----------------------------------------------------

    assert (
        nba.ai_reasoning
        is not None
    )

    assert (
        "LBIT"
        in nba.ai_reasoning
    )

    assert (
        "Requested demo"
        in nba.ai_reasoning
    )

    assert (
        f"Level {result['lbit']['level']}"
        in nba.ai_reasoning
    )

    assert (
        result["lbit"]["category"]
        in nba.ai_reasoning
    )

    # -----------------------------------------------------
    # VERIFY RETURNED NBA
    # -----------------------------------------------------

    assert (
        result["next_best_action"]
        is not None
    )

    assert (
        result[
            "next_best_action"
        ]["ai_reasoning"]
        == nba.ai_reasoning
    )