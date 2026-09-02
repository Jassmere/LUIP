import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app

from app.database import (
    get_db,
    Company,
    BuyingIntentSignal,
    BuyingActivity,
    CompanyScore,
    NextBestAction,
)

from app.db.base import Base


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
# DATABASE OVERRIDE
# =========================================================

def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


# =========================================================
# TEST DATABASE INITIALIZATION
# =========================================================

@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    """
    Create the complete SQLite test database once for the
    entire Buying Signal test module.

    The database is intentionally not dropped between tests.
    Individual tests clean up their own records where required.

    This prevents other test modules from leaving the shared
    FastAPI dependency override pointing at a database whose
    tables have already been dropped.
    """

    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


# =========================================================
# DATABASE OVERRIDE FIXTURE
# =========================================================

@pytest.fixture(autouse=True)
def apply_database_override():
    """
    Re-apply the Buying Signal test database override before
    every test.

    The full LUIP test suite contains multiple modules that
    use their own database overrides. Without re-applying this
    override, another test module can replace get_db and cause
    Buying Signal tests to connect to the production database.

    This is the reason the Buying Signal tests can pass
    individually but fail when the complete suite is executed.
    """

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.pop(get_db, None)


# =========================================================
# TEST CLIENT
# =========================================================

client = TestClient(app)


# =========================================================
# DATABASE FIXTURE
# =========================================================

@pytest.fixture
def db():
    """
    Provide a database session for each test.

    Tables remain available for the entire module because the
    database itself is initialized at session scope.
    """

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
    """
    Create an isolated test company.
    """

    test_company = Company(
        name="LUIP Buying Signal Router Test Company",
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
# BUYING SIGNAL STATUS
# =========================================================

def test_buying_signal_status():

    response = client.get(
        "/buying-signals/status"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == (
        "LUIP Buying Signal Service"
    )

    assert "version" in data


# =========================================================
# CREATE BUYING SIGNAL
# =========================================================

def test_create_buying_signal(
    company,
):

    response = client.post(
        "/buying-signals/",
        json={
            "company_id": company.id,
            "signal_name": "Requested Demo",
            "signal_category": "Demo Request",
            "score": 95,
            "confidence": 95,
            "source": "Test",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["company_id"] == company.id
    assert data["signal_name"] == "Requested Demo"


# =========================================================
# LBIT CLASSIFICATION
# =========================================================

def test_create_buying_signal_lbit_classification(
    company,
):

    response = client.post(
        "/buying-signals/",
        json={
            "company_id": company.id,
            "signal_name": "requested_demo",
            "signal_category": "Demo Request",
            "score": 95,
            "confidence": 95,
            "source": "Test",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert data["lbit_level"] == 5

    assert data["lbit_category"] == (
        "Immediate Buying Intent"
    )

    assert data["lbit_score"] == 95

    assert data["lbit_confidence"] == 95


# =========================================================
# STORES SIGNAL
# =========================================================

def test_create_buying_signal_stores_signal(
    db,
    company,
):

    response = client.post(
        "/buying-signals/",
        json={
            "company_id": company.id,
            "signal_name": "Requested Demo",
            "signal_category": "Demo Request",
            "score": 95,
            "confidence": 95,
            "source": "Test",
        },
    )

    assert response.status_code == 200

    signal = (
        db.query(BuyingIntentSignal)
        .filter(
            BuyingIntentSignal.company_id
            == company.id
        )
        .first()
    )

    assert signal is not None

    assert signal.signal_name == "Requested Demo"

    assert signal.signal_category == "Demo Request"

    assert signal.company_id == company.id


# =========================================================
# CREATES BUYING ACTIVITY
# =========================================================

def test_create_buying_signal_creates_activity(
    db,
    company,
):

    response = client.post(
        "/buying-signals/",
        json={
            "company_id": company.id,
            "signal_name": "Requested Demo",
            "signal_category": "Demo Request",
            "score": 95,
            "confidence": 95,
            "source": "Test",
        },
    )

    assert response.status_code == 200

    activities = (
        db.query(BuyingActivity)
        .filter(
            BuyingActivity.company_id
            == company.id
        )
        .all()
    )

    assert len(activities) >= 1


# =========================================================
# UPDATES COMPANY SCORE
# =========================================================

def test_create_buying_signal_updates_company_score(
    db,
    company,
):

    response = client.post(
        "/buying-signals/",
        json={
            "company_id": company.id,
            "signal_name": "Requested Demo",
            "signal_category": "Demo Request",
            "score": 95,
            "confidence": 95,
            "source": "Test",
        },
    )

    assert response.status_code == 200

    company_score = (
        db.query(CompanyScore)
        .filter(
            CompanyScore.company_id
            == company.id
        )
        .first()
    )

    assert company_score is not None


# =========================================================
# CREATES NEXT BEST ACTION
# =========================================================

def test_create_buying_signal_creates_next_best_action(
    db,
    company,
):

    response = client.post(
        "/buying-signals/",
        json={
            "company_id": company.id,
            "signal_name": "Requested Demo",
            "signal_category": "Demo Request",
            "score": 95,
            "confidence": 95,
            "source": "Test",
        },
    )

    assert response.status_code == 200

    actions = (
        db.query(NextBestAction)
        .filter(
            NextBestAction.company_id
            == company.id
        )
        .all()
    )

    assert len(actions) >= 1


# =========================================================
# COMPLETE RESPONSE
# =========================================================

def test_create_buying_signal_complete_response(
    company,
):

    response = client.post(
        "/buying-signals/",
        json={
            "company_id": company.id,
            "signal_name": "Requested Demo",
            "signal_category": "Demo Request",
            "score": 95,
            "confidence": 95,
            "source": "Test",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert data["company_id"] == company.id

    assert "signal_name" in data
    assert "signal_category" in data
    assert "score" in data
    assert "confidence" in data

    assert "lbit_level" in data
    assert "lbit_category" in data
    assert "lbit_score" in data
    assert "lbit_confidence" in data


# =========================================================
# UNCLASSIFIED BUYING SIGNAL
# =========================================================

def test_create_unclassified_buying_signal(
    company,
):

    response = client.post(
        "/buying-signals/",
        json={
            "company_id": company.id,
            "signal_name": "General Website Visit",
            "signal_category": "Website Intelligence",
            "score": 40,
            "confidence": 70,
            "source": "Test",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert data["lbit_level"] is None

    assert data["lbit_category"] is None


# =========================================================
# INVALID COMPANY
# =========================================================

def test_create_buying_signal_invalid_company():

    response = client.post(
        "/buying-signals/",
        json={
            "company_id": 999999,
            "signal_name": "Requested Demo",
            "signal_category": "Demo Request",
            "score": 95,
            "confidence": 95,
            "source": "Test",
        },
    )

    assert response.status_code in [404, 400]


# =========================================================
# EMPTY SIGNAL NAME
# =========================================================

def test_create_buying_signal_empty_name(
    company,
):

    response = client.post(
        "/buying-signals/",
        json={
            "company_id": company.id,
            "signal_name": "",
            "signal_category": "Demo Request",
            "score": 95,
            "confidence": 95,
            "source": "Test",
        },
    )

    assert response.status_code in [400, 422]


# =========================================================
# EMPTY SIGNAL CATEGORY
# =========================================================

def test_create_buying_signal_empty_category(
    company,
):

    response = client.post(
        "/buying-signals/",
        json={
            "company_id": company.id,
            "signal_name": "Requested Demo",
            "signal_category": "",
            "score": 95,
            "confidence": 95,
            "source": "Test",
        },
    )

    assert response.status_code in [400, 422]


# =========================================================
# SCORE CLAMPING
# =========================================================

def test_buying_signal_score_is_clamped(
    company,
):

    response = client.post(
        "/buying-signals/",
        json={
            "company_id": company.id,
            "signal_name": "Requested Demo",
            "signal_category": "Demo Request",
            "score": 150,
            "confidence": 95,
            "source": "Test",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["score"] <= 100


# =========================================================
# CONFIDENCE CLAMPING
# =========================================================

def test_buying_signal_confidence_is_clamped(
    company,
):

    response = client.post(
        "/buying-signals/",
        json={
            "company_id": company.id,
            "signal_name": "Requested Demo",
            "signal_category": "Demo Request",
            "score": 95,
            "confidence": 150,
            "source": "Test",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["confidence"] <= 100