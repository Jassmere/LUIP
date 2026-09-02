import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base

# =========================================================
# IMPORT MODELS
#
# These imports ensure all required tables and foreign-key
# dependencies are registered with Base.metadata before
# create_all() is executed.
# =========================================================

from app.models.company import Company
from app.models.buying_activity import BuyingActivity
from app.models.buying_intent_signal import BuyingIntentSignal
from app.models.company_score import CompanyScore
from app.models.next_best_action import NextBestAction
from app.models.decision_maker import DecisionMaker

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
            "LUIP LBIT NBA Propagation "
            "Test Company"
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

    # -----------------------------------------------------
    # CLEANUP
    # -----------------------------------------------------

    db.query(
        NextBestAction
    ).filter(
        NextBestAction.company_id
        == test_company.id
    ).delete(
        synchronize_session=False
    )

    db.query(
        CompanyScore
    ).filter(
        CompanyScore.company_id
        == test_company.id
    ).delete(
        synchronize_session=False
    )

    db.query(
        BuyingActivity
    ).filter(
        BuyingActivity.company_id
        == test_company.id
    ).delete(
        synchronize_session=False
    )

    db.query(
        BuyingIntentSignal
    ).filter(
        BuyingIntentSignal.company_id
        == test_company.id
    ).delete(
        synchronize_session=False
    )

    db.query(
        Company
    ).filter(
        Company.id
        == test_company.id
    ).delete(
        synchronize_session=False
    )

    db.commit()


# =========================================================
# LBIT → NBA PROPAGATION
# =========================================================

def test_lbit_context_is_propagated_to_next_best_action(
    db,
    company,
):
    """
    Verify that a classified buying signal passes its
    LBIT context into the Next Best Action engine.

    Pipeline under test:

        Buying Signal
             ↓
           LBIT
             ↓
       Company Score
             ↓
      Next Best Action
             ↓
      Explainable Reasoning
    """

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=company.id,
        signal_name="Requested demo",
        signal_category="Direct Buying Intent",
        source="Test",
        source_url="https://example.com",
        evidence=(
            "Test company requested a product "
            "demonstration."
        ),
        score=95,
        confidence=95,
    )

    # -----------------------------------------------------
    # VERIFY SIGNAL CREATION
    # -----------------------------------------------------

    assert result["success"] is True

    # -----------------------------------------------------
    # VERIFY LBIT CLASSIFICATION
    # -----------------------------------------------------

    assert result["lbit"]["classified"] is True

    assert result["lbit"]["level"] is not None

    assert result["lbit"]["category"] is not None

    assert result["lbit"]["score"] is not None

    assert result["lbit"]["confidence"] is not None

    # -----------------------------------------------------
    # VERIFY NEXT BEST ACTION
    # -----------------------------------------------------

    nba = (
        db.query(
            NextBestAction
        )
        .filter(
            NextBestAction.company_id
            == company.id
        )
        .filter(
            NextBestAction.status
            == "Pending"
        )
        .first()
    )

    assert nba is not None

    assert nba.priority == "Critical"

    assert nba.action_type == (
        "Call immediately"
    )

    # -----------------------------------------------------
    # VERIFY EXPLAINABLE REASONING
    # -----------------------------------------------------

    assert nba.ai_reasoning is not None

    assert "LBIT" in nba.ai_reasoning

    assert "Requested demo" in (
        nba.ai_reasoning
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
    # VERIFY RESULT CONTAINS REASONING
    # -----------------------------------------------------

    assert (
        result[
            "next_best_action"
        ]["ai_reasoning"]
        is not None
    )

    assert (
        result[
            "next_best_action"
        ]["ai_reasoning"]
        == nba.ai_reasoning
    )