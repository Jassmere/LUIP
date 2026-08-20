import pytest

from app.database import (
    Company,
    BuyingActivity,
    BuyingIntentSignal,
    CompanyScore,
    NextBestAction,
)

from app.db.session import SessionLocal

from app.services.buying_signal_service import (
    BuyingSignalService,
)


@pytest.fixture
def db():
    session = SessionLocal()

    try:
        yield session

    finally:
        session.rollback()
        session.close()


@pytest.fixture
def company(db):
    test_company = Company(
        name="LUIP Buying Signal Service Test Company",
        website="https://example.com",
        industry="Legal Technology",
        country="India",
        city="Mumbai",
        active=True,
    )

    db.add(test_company)
    db.commit()
    db.refresh(test_company)

    try:
        yield test_company

    finally:
        db.query(NextBestAction).filter(
            NextBestAction.company_id == test_company.id
        ).delete(
            synchronize_session=False
        )

        db.query(CompanyScore).filter(
            CompanyScore.company_id == test_company.id
        ).delete(
            synchronize_session=False
        )

        db.query(BuyingActivity).filter(
            BuyingActivity.company_id == test_company.id
        ).delete(
            synchronize_session=False
        )

        db.query(BuyingIntentSignal).filter(
            BuyingIntentSignal.company_id == test_company.id
        ).delete(
            synchronize_session=False
        )

        db.query(Company).filter(
            Company.id == test_company.id
        ).delete(
            synchronize_session=False
        )

        db.commit()


# =========================================================
# VERSION
# =========================================================


def test_buying_signal_service_version():
    assert BuyingSignalService.VERSION == "1.3.0"


# =========================================================
# INVALID COMPANY
# =========================================================


def test_create_signal_company_not_found(db):

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=999999999,
        signal_name="requested_demo",
        signal_category="Demo Request",
        score=95.0,
        confidence=100.0,
    )

    assert result["success"] is False

    assert (
        result["error"]
        == "Company 999999999 not found."
    )


# =========================================================
# REQUIRED SIGNAL NAME
# =========================================================


@pytest.mark.parametrize(
    "signal_name",
    [
        None,
        "",
        "   ",
    ],
)
def test_create_signal_requires_signal_name(
    db,
    company,
    signal_name,
):

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=company.id,
        signal_name=signal_name,
        signal_category="Demo Request",
        score=50.0,
        confidence=100.0,
    )

    assert result["success"] is False

    assert result["error"] == (
        "signal_name is required"
    )


# =========================================================
# REQUIRED SIGNAL CATEGORY
# =========================================================


@pytest.mark.parametrize(
    "signal_category",
    [
        None,
        "",
        "   ",
    ],
)
def test_create_signal_requires_signal_category(
    db,
    company,
    signal_category,
):

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=company.id,
        signal_name="website_visit",
        signal_category=signal_category,
        score=50.0,
        confidence=100.0,
    )

    assert result["success"] is False

    assert result["error"] == (
        "signal_category is required"
    )


# =========================================================
# SCORE NORMALIZATION
# =========================================================


def test_score_is_clamped_to_zero(
    db,
    company,
):

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=company.id,
        signal_name="website_visit",
        signal_category="Website Intelligence",
        score=-50.0,
        confidence=50.0,
    )

    assert result["success"] is True

    assert result["signal"]["score"] == 0.0

    assert (
        result["buying_activity"]["buying_score"]
        == 0.0
    )


def test_score_is_clamped_to_100(
    db,
    company,
):

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=company.id,
        signal_name="website_visit",
        signal_category="Website Intelligence",
        score=150.0,
        confidence=50.0,
    )

    assert result["success"] is True

    assert result["signal"]["score"] == 100.0

    assert (
        result["buying_activity"]["buying_score"]
        == 100.0
    )


def test_invalid_score_defaults_to_zero(
    db,
    company,
):

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=company.id,
        signal_name="website_visit",
        signal_category="Website Intelligence",
        score="not-a-number",
        confidence=50.0,
    )

    assert result["success"] is True

    assert result["signal"]["score"] == 0.0


# =========================================================
# CONFIDENCE NORMALIZATION
# =========================================================


def test_confidence_is_clamped_to_zero(
    db,
    company,
):

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=company.id,
        signal_name="website_visit",
        signal_category="Website Intelligence",
        score=50.0,
        confidence=-25.0,
    )

    assert result["success"] is True

    assert result["signal"]["confidence"] == 0.0


def test_confidence_is_clamped_to_100(
    db,
    company,
):

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=company.id,
        signal_name="website_visit",
        signal_category="Website Intelligence",
        score=50.0,
        confidence=150.0,
    )

    assert result["success"] is True

    assert result["signal"]["confidence"] == 100.0


def test_invalid_confidence_defaults_to_100(
    db,
    company,
):

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=company.id,
        signal_name="website_visit",
        signal_category="Website Intelligence",
        score=50.0,
        confidence="invalid",
    )

    assert result["success"] is True

    assert result["signal"]["confidence"] == 100.0


# =========================================================
# TEXT NORMALIZATION
# =========================================================


def test_text_values_are_trimmed(
    db,
    company,
):

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=company.id,
        signal_name="  website_visit  ",
        signal_category="  Website Intelligence  ",
        source="  test_source  ",
        source_url="  https://example.com  ",
        evidence="  Test evidence  ",
        score=50.0,
        confidence=80.0,
    )

    assert result["success"] is True

    assert (
        result["signal"]["signal_name"]
        == "website_visit"
    )

    assert (
        result["signal"]["signal_category"]
        == "Website Intelligence"
    )

    assert (
        result["signal"]["source"]
        == "test_source"
    )

    assert (
        result["signal"]["source_url"]
        == "https://example.com"
    )

    assert (
        result["signal"]["evidence"]
        == "Test evidence"
    )


# =========================================================
# UNCLASSIFIED LBIT SIGNAL
# =========================================================


def test_unclassified_signal_remains_valid(
    db,
    company,
):

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=company.id,
        signal_name="website_visit",
        signal_category="Website Intelligence",
        source="test",
        evidence="General website activity.",
        score=50.0,
        confidence=80.0,
    )

    assert result["success"] is True

    assert result["lbit"]["classified"] is False

    assert result["lbit"]["level"] is None

    assert result["lbit"]["category"] is None

    assert result["lbit"]["score"] is None

    assert result["lbit"]["confidence"] is None


# =========================================================
# ESTABLISHED LBIT SIGNAL
# =========================================================


def test_level_5_signal_is_classified(
    db,
    company,
):

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=company.id,
        signal_name="requested_demo",
        signal_category="Demo Request",
        source="test",
        score=95.0,
        confidence=100.0,
    )

    assert result["success"] is True

    assert result["lbit"]["classified"] is True

    assert result["lbit"]["level"] == 5

    assert (
        result["lbit"]["category"]
        == "Immediate Buying Intent"
    )

    assert result["lbit"]["score"] == 95.0

    assert result["lbit"]["confidence"] == 100.0


# =========================================================
# DATABASE SIGNAL RECORD
# =========================================================


def test_buying_intent_signal_is_saved(
    db,
    company,
):

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=company.id,
        signal_name="requested_demo",
        signal_category="Demo Request",
        source="test",
        source_url="https://example.com/demo",
        evidence="Demo requested.",
        score=95.0,
        confidence=100.0,
    )

    assert result["success"] is True

    signal = (
        db.query(BuyingIntentSignal)
        .filter(
            BuyingIntentSignal.id
            == result["signal"]["id"]
        )
        .first()
    )

    assert signal is not None

    assert signal.company_id == company.id

    assert signal.signal_name == "requested_demo"

    assert signal.signal_category == "Demo Request"

    assert signal.source == "test"

    assert (
        signal.source_url
        == "https://example.com/demo"
    )

    assert signal.evidence == "Demo requested."

    assert signal.score == 95.0

    assert signal.confidence == 100.0

    assert signal.lbit_level == 5

    assert (
        signal.lbit_category
        == "Immediate Buying Intent"
    )


# =========================================================
# DATABASE BUYING ACTIVITY
# =========================================================


def test_buying_activity_is_saved(
    db,
    company,
):

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=company.id,
        signal_name="requested_demo",
        signal_category="Demo Request",
        source="test",
        source_url="https://example.com/demo",
        evidence="Demo requested.",
        score=95.0,
        confidence=100.0,
    )

    assert result["success"] is True

    activity = (
        db.query(BuyingActivity)
        .filter(
            BuyingActivity.id
            == result["buying_activity"]["id"]
        )
        .first()
    )

    assert activity is not None

    assert activity.company_id == company.id

    assert activity.activity_type == "Demo Request"

    assert activity.activity_source == "test"

    assert activity.title == "requested_demo"

    assert activity.description == (
        "Demo requested."
    )

    assert activity.url == (
        "https://example.com/demo"
    )

    assert activity.buying_score == 95.0

    assert activity.confidence == 100.0

    assert activity.processed is False


# =========================================================
# COMPANY SCORE
# =========================================================


def test_company_score_is_generated(
    db,
    company,
):

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=company.id,
        signal_name="requested_demo",
        signal_category="Demo Request",
        score=95.0,
        confidence=100.0,
    )

    assert result["success"] is True

    assert (
        result["company_score"]
        ["buying_intent_score"]
        == 95.0
    )

    assert (
        result["company_score"]
        ["confidence"]
        == 100.0
    )

    assert (
        result["company_score"]
        ["priority"]
        == "High"
    )

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


# =========================================================
# NEXT BEST ACTION
# =========================================================


def test_next_best_action_is_generated(
    db,
    company,
):

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=company.id,
        signal_name="requested_demo",
        signal_category="Demo Request",
        score=95.0,
        confidence=100.0,
    )

    assert result["success"] is True

    action = result["next_best_action"]

    assert action["id"] is not None

    assert action["priority"] == "Critical"

    assert action["action_type"] == (
        "Call immediately"
    )

    assert (
        action["recommended_within_hours"]
        == 1
    )

    assert action["status"] == "Pending"


# =========================================================
# RECORD SIGNAL BACKWARD COMPATIBILITY
# =========================================================


def test_record_signal_is_backward_compatible(
    db,
    company,
):

    result = BuyingSignalService.record_signal(
        db=db,
        company_id=company.id,
        signal_name="requested_demo",
        signal_category="Demo Request",
        source="legacy_test",
        score=95.0,
        confidence=100.0,
    )

    assert result["success"] is True

    assert result["version"] == "1.3.0"

    assert result["lbit"]["classified"] is True

    assert result["lbit"]["level"] == 5


# =========================================================
# GET COMPANY SIGNALS
# =========================================================


def test_get_company_signals(
    db,
    company,
):

    create_result = (
        BuyingSignalService.create_signal(
            db=db,
            company_id=company.id,
            signal_name="requested_demo",
            signal_category="Demo Request",
            source="test",
            score=95.0,
            confidence=100.0,
        )
    )

    assert create_result["success"] is True

    result = (
        BuyingSignalService.get_company_signals(
            db=db,
            company_id=company.id,
        )
    )

    assert result["success"] is True

    assert result["company_id"] == company.id

    assert result["company"] == company.name

    assert len(result["signals"]) >= 1

    signal = result["signals"][0]

    assert signal["signal_name"] == (
        "requested_demo"
    )

    assert signal["signal_category"] == (
        "Demo Request"
    )

    assert signal["lbit"]["classified"] is True

    assert signal["lbit"]["level"] == 5


# =========================================================
# GET COMPANY ACTIVITIES
# =========================================================


def test_get_company_activities(
    db,
    company,
):

    create_result = (
        BuyingSignalService.create_signal(
            db=db,
            company_id=company.id,
            signal_name="requested_demo",
            signal_category="Demo Request",
            source="test",
            score=95.0,
            confidence=100.0,
        )
    )

    assert create_result["success"] is True

    result = (
        BuyingSignalService.get_company_activities(
            db=db,
            company_id=company.id,
        )
    )

    assert result["success"] is True

    assert result["company_id"] == company.id

    assert result["company"] == company.name

    assert len(result["activities"]) >= 1

    activity = result["activities"][0]

    assert activity["activity_type"] == (
        "Demo Request"
    )

    assert activity["title"] == (
        "requested_demo"
    )

    assert activity["buying_score"] == 95.0


# =========================================================
# COMPANY NOT FOUND - GET SIGNALS
# =========================================================


def test_get_company_signals_company_not_found(
    db,
):

    result = (
        BuyingSignalService.get_company_signals(
            db=db,
            company_id=999999999,
        )
    )

    assert result["success"] is False

    assert result["error"] == "Company not found"


# =========================================================
# COMPANY NOT FOUND - GET ACTIVITIES
# =========================================================


def test_get_company_activities_company_not_found(
    db,
):

    result = (
        BuyingSignalService.get_company_activities(
            db=db,
            company_id=999999999,
        )
    )

    assert result["success"] is False

    assert result["error"] == "Company not found"