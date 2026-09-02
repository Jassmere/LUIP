import pytest

from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app

from app.database import (
    get_db,
    Company,
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
# DATABASE INITIALISATION
# =========================================================

@pytest.fixture(
    scope="session",
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
# DATABASE OVERRIDE FIXTURE
# =========================================================

@pytest.fixture(
    autouse=True,
)
def apply_database_override():

    app.dependency_overrides[
        get_db
    ] = override_get_db

    yield

    app.dependency_overrides.pop(
        get_db,
        None,
    )


# =========================================================
# TEST CLIENT
# =========================================================

client = TestClient(app)


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
            "LUIP Buying Intelligence "
            "Router Test Company"
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
        Company
    ).filter(
        Company.id
        == test_company.id
    ).delete(
        synchronize_session=False
    )

    db.commit()


# =========================================================
# LIST COMPANIES
# =========================================================

def test_list_companies(
    company,
):

    response = client.get(
        "/buying-intelligence/companies"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(
        data,
        list,
    )

    matching = [
        item
        for item in data
        if item.get(
            "company_id"
        ) == company.id
    ]

    assert len(matching) == 1

    result = matching[0]

    assert result["company"] == (
        company.name
    )

    assert result["buying_intent_score"] == 0

    assert result["confidence"] == 0

    assert result["priority"] == "Low"


# =========================================================
# COMPANY DETAILS
# =========================================================

def test_company_details(
    company,
):

    response = client.get(
        f"/buying-intelligence/company/{company.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == (
        company.id
    )

    assert data["company"] == (
        company.name
    )

    assert data["website"] == (
        company.website
    )

    assert data["industry"] == (
        company.industry
    )

    assert data["country"] == (
        company.country
    )

    assert data["city"] == (
        company.city
    )

    assert data["buying_intent_score"] == 0

    assert data["confidence"] == 0

    assert data["priority"] == "Low"

    assert data["activities"] == []


# =========================================================
# COMPANY NOT FOUND
# =========================================================

def test_company_details_not_found():

    response = client.get(
        "/buying-intelligence/company/999999"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["error"] == (
        "Company not found"
    )


# =========================================================
# TOP TARGETS WITHOUT SCORE
# =========================================================

def test_top_targets_requires_company_score(
    company,
):

    response = client.get(
        "/buying-intelligence/top-targets"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(
        data,
        list,
    )

    matching = [
        item
        for item in data
        if item.get(
            "company_id"
        ) == company.id
    ]

    assert matching == []


# =========================================================
# TOP TARGETS WITH SCORE
# =========================================================

def test_top_targets_returns_nba(
    db,
    company,
):

    company_score = CompanyScore(
        company_id=company.id,
        buying_intent_score=95,
        confidence=95,
        priority="High",
    )

    db.add(company_score)

    db.commit()

    response = client.get(
        "/buying-intelligence/top-targets"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(
        data,
        list,
    )

    matching = [
        item
        for item in data
        if item.get(
            "company_id"
        ) == company.id
    ]

    assert len(matching) == 1

    result = matching[0]

    assert result["company"] == (
        company.name
    )

    assert result["score"] == 95.0

    assert result["confidence"] == 95.0

    assert "next_best_action" in result

    assert result[
        "next_best_action"
    ]["company"] == company.name

    assert result[
        "next_best_action"
    ]["score"] == 95.0

    assert result[
        "next_best_action"
    ]["priority"] == "Critical"

    assert result[
        "next_best_action"
    ]["action"] == (
        "Call immediately"
    )

    assert (
        result["next_best_action_id"]
        is not None
    )

    assert result[
        "next_best_action_status"
    ] == "Pending"


# =========================================================
# VERIFY NBA PERSISTENCE
# =========================================================

def test_top_targets_persists_next_best_action(
    db,
    company,
):

    company_score = CompanyScore(
        company_id=company.id,
        buying_intent_score=85,
        confidence=90,
        priority="High",
    )

    db.add(company_score)

    db.commit()

    response = client.get(
        "/buying-intelligence/top-targets"
    )

    assert response.status_code == 200

    actions = (
        db.query(
            NextBestAction
        )
        .filter(
            NextBestAction.company_id
            == company.id
        )
        .all()
    )

    assert len(actions) == 1

    action = actions[0]

    assert action.company_id == (
        company.id
    )

    assert action.status == "Pending"

    assert action.priority == "High"

    assert action.action_type == (
        "Book product demonstration"
    )

    assert action.recommended_within_hours == 4

    assert action.explanation is not None


# =========================================================
# VERIFY EXISTING PENDING ACTION IS REFRESHED
# =========================================================

def test_top_targets_refreshes_existing_pending_action(
    db,
    company,
):

    existing_action = NextBestAction(
        company_id=company.id,
        action_type="Continue monitoring",
        priority="Cold",
        recommended_within_hours=168,
        explanation="Old explanation",
        status="Pending",
    )

    db.add(existing_action)

    db.commit()

    db.refresh(existing_action)

    company_score = CompanyScore(
        company_id=company.id,
        buying_intent_score=95,
        confidence=95,
        priority="High",
    )

    db.add(company_score)

    db.commit()

    response = client.get(
        "/buying-intelligence/top-targets"
    )

    assert response.status_code == 200

    db.refresh(existing_action)

    assert existing_action.status == (
        "Pending"
    )

    assert existing_action.priority == (
        "Critical"
    )

    assert existing_action.action_type == (
        "Call immediately"
    )

    assert existing_action.recommended_within_hours == 1

    actions = (
        db.query(
            NextBestAction
        )
        .filter(
            NextBestAction.company_id
            == company.id
        )
        .all()
    )

    assert len(actions) == 1


# =========================================================
# TOP TARGETS SCORE ORDER
# =========================================================

def test_top_targets_are_ordered_by_score(
    db,
):

    low_company = Company(
        name="LUIP Low Score Company",
        website="https://low.example.com",
        industry="Legal Technology",
        country="India",
        city="Delhi",
        active=True,
    )

    high_company = Company(
        name="LUIP High Score Company",
        website="https://high.example.com",
        industry="Legal Technology",
        country="India",
        city="Mumbai",
        active=True,
    )

    db.add(
        low_company
    )

    db.add(
        high_company
    )

    db.commit()

    db.refresh(
        low_company
    )

    db.refresh(
        high_company
    )

    db.add(
        CompanyScore(
            company_id=low_company.id,
            buying_intent_score=50,
            confidence=70,
            priority="Low",
        )
    )

    db.add(
        CompanyScore(
            company_id=high_company.id,
            buying_intent_score=95,
            confidence=95,
            priority="High",
        )
    )

    db.commit()

    response = client.get(
        "/buying-intelligence/top-targets"
    )

    assert response.status_code == 200

    data = response.json()

    high_index = next(
        index
        for index, item in enumerate(data)
        if item["company_id"]
        == high_company.id
    )

    low_index = next(
        index
        for index, item in enumerate(data)
        if item["company_id"]
        == low_company.id
    )

    assert high_index < low_index

    # -----------------------------------------------------
    # CLEANUP
    # -----------------------------------------------------

    db.query(
        NextBestAction
    ).filter(
        NextBestAction.company_id.in_(
            [
                low_company.id,
                high_company.id,
            ]
        )
    ).delete(
        synchronize_session=False
    )

    db.query(
        CompanyScore
    ).filter(
        CompanyScore.company_id.in_(
            [
                low_company.id,
                high_company.id,
            ]
        )
    ).delete(
        synchronize_session=False
    )

    db.query(
        Company
    ).filter(
        Company.id.in_(
            [
                low_company.id,
                high_company.id,
            ]
        )
    ).delete(
        synchronize_session=False
    )

    db.commit()