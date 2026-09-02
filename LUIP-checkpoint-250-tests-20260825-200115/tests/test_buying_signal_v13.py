import pytest

from app.database import (
    Company,
    CompanyScore,
    BuyingActivity,
    BuyingIntentSignal,
    NextBestAction,
)

from app.db.session import SessionLocal

from app.services.buying_signal_service import (
    BuyingSignalService,
)

from app.services.buying_intelligence_service import (
    BuyingIntelligenceService,
)

from app.services.next_best_action_service import (
    NextBestActionService,
)


@pytest.fixture
def db():
    session = SessionLocal()

    try:
        yield session

    finally:
        session.rollback()
        session.close()


def test_v13_buying_signal_pipeline(db):
    """
    LUIP v1.3 integration test.

    Verifies the complete buying-intelligence pipeline:

        Company
            ->
        BuyingSignalService
            ->
        BuyingIntentSignal
            ->
        LBITService
            ->
        BuyingActivity
            ->
        BuyingIntelligenceService
            ->
        CompanyScore
            ->
        NextBestActionService
            ->
        NextBestAction
    """

    # ---------------------------------------------------------
    # CREATE TEST COMPANY
    # ---------------------------------------------------------

    company = Company(
        name="LUIP V1.3 Integration Test Company",
        website="https://example.com",
        industry="Legal Technology",
        country="India",
        city="Mumbai",
        active=True,
    )

    db.add(company)
    db.commit()
    db.refresh(company)

    try:

        # -----------------------------------------------------
        # 1. CREATE BUYING SIGNAL
        # -----------------------------------------------------

        result = BuyingSignalService.create_signal(
            db=db,
            company_id=company.id,
            signal_name="requested_demo",
            signal_category="Demo Request",
            source="integration_test",
            source_url="https://example.com/demo",
            evidence=(
                "Test company requested a product "
                "demonstration."
            ),
            score=95.0,
            confidence=100.0,
        )

        # -----------------------------------------------------
        # VERIFY BASIC RESULT
        # -----------------------------------------------------

        assert result["success"] is True

        assert result["version"] == "1.3.0"

        # -----------------------------------------------------
        # 2. VERIFY LBIT CLASSIFICATION
        # -----------------------------------------------------

        assert result["lbit"]["classified"] is True

        assert result["lbit"]["level"] == 5

        assert (
            result["lbit"]["category"]
            == "Immediate Buying Intent"
        )

        assert result["lbit"]["score"] == 95.0

        assert result["lbit"]["confidence"] == 100.0

        # -----------------------------------------------------
        # 3. VERIFY BUYING INTENT SIGNAL
        # -----------------------------------------------------

        signal = (
            db.query(BuyingIntentSignal)
            .filter(
                BuyingIntentSignal.company_id
                == company.id
            )
            .first()
        )

        assert signal is not None

        assert signal.signal_name == "requested_demo"

        assert signal.signal_category == "Demo Request"

        assert signal.score == 95.0

        assert signal.confidence == 100.0

        # -----------------------------------------------------
        # VERIFY LBIT DATA STORED
        # -----------------------------------------------------

        assert signal.lbit_level == 5

        assert (
            signal.lbit_category
            == "Immediate Buying Intent"
        )

        assert signal.lbit_score == 95.0

        assert signal.lbit_confidence == 100.0

        # -----------------------------------------------------
        # 4. VERIFY BUYING ACTIVITY
        # -----------------------------------------------------

        activity = (
            db.query(BuyingActivity)
            .filter(
                BuyingActivity.company_id
                == company.id
            )
            .first()
        )

        assert activity is not None

        assert activity.activity_type == "Demo Request"

        assert activity.activity_source == (
            "integration_test"
        )

        assert activity.title == "requested_demo"

        assert activity.buying_score == 95.0

        assert activity.confidence == 100.0

        assert activity.processed is False

        # -----------------------------------------------------
        # 5. CALCULATE COMPANY BUYING SCORE
        # -----------------------------------------------------

        company_score = (
            BuyingIntelligenceService.calculate_company_score(
                db=db,
                company_id=company.id,
            )
        )

        assert company_score is not None

        assert (
            company_score.buying_intent_score
            == 95.0
        )

        assert company_score.confidence == 100.0

        assert company_score.priority == "High"

        # -----------------------------------------------------
        # 6. VERIFY COMPANY SCORE IN DATABASE
        # -----------------------------------------------------

        saved_score = (
            db.query(CompanyScore)
            .filter(
                CompanyScore.company_id
                == company.id
            )
            .first()
        )

        assert saved_score is not None

        assert (
            saved_score.buying_intent_score
            == 95.0
        )

        assert saved_score.confidence == 100.0

        assert saved_score.priority == "High"

        # -----------------------------------------------------
        # 7. CREATE NEXT BEST ACTION
        # -----------------------------------------------------

        action = (
            NextBestActionService.create_action(
                db=db,
                company_id=company.id,
                score=company_score.buying_intent_score,
            )
        )

        assert action is not None

        assert action.priority == "Critical"

        assert action.action_type == (
            "Call immediately"
        )

        assert (
            action.recommended_within_hours
            == 1
        )

        assert action.status == "Pending"

        # -----------------------------------------------------
        # 8. VERIFY NEXT BEST ACTION IN DATABASE
        # -----------------------------------------------------

        saved_action = (
            db.query(NextBestAction)
            .filter(
                NextBestAction.company_id
                == company.id
            )
            .first()
        )

        assert saved_action is not None

        assert saved_action.priority == "Critical"

        assert saved_action.action_type == (
            "Call immediately"
        )

        assert (
            saved_action.recommended_within_hours
            == 1
        )

        assert saved_action.status == "Pending"

    finally:

        # -----------------------------------------------------
        # CLEANUP TEST DATA
        # -----------------------------------------------------

        db.query(NextBestAction).filter(
            NextBestAction.company_id
            == company.id
        ).delete(
            synchronize_session=False
        )

        db.query(CompanyScore).filter(
            CompanyScore.company_id
            == company.id
        ).delete(
            synchronize_session=False
        )

        db.query(BuyingActivity).filter(
            BuyingActivity.company_id
            == company.id
        ).delete(
            synchronize_session=False
        )

        db.query(BuyingIntentSignal).filter(
            BuyingIntentSignal.company_id
            == company.id
        ).delete(
            synchronize_session=False
        )

        db.query(Company).filter(
            Company.id
            == company.id
        ).delete(
            synchronize_session=False
        )

        db.commit()