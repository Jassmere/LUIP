"""
LUIP Discovery Router Tests.

Tests the FastAPI Discovery API layer without changing
the underlying Discovery Engine or Buying Signal pipeline.

Version: 1.0.9
"""

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.db.base import Base


# ---------------------------------------------------------
# TEST DATABASE
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# DATABASE OVERRIDE
# ---------------------------------------------------------

def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# ---------------------------------------------------------
# TEST CLIENT
# ---------------------------------------------------------

client = TestClient(app)


# ---------------------------------------------------------
# FIXTURE
# ---------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_database():
    """
    Create a clean database for every test.
    """

    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------
# DISCOVERY STATUS
# ---------------------------------------------------------

def test_discovery_status():
    response = client.get(
        "/discovery/status"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["engine"] == "LUIP Discovery Engine"
    assert data["version"] == "1.0.9"
    assert data["status"] == "Running"

    assert "scanners" in data
    assert "scan_statuses" in data


# ---------------------------------------------------------
# DISCOVER COMPANY
# ---------------------------------------------------------

def test_discover_company():
    response = client.post(
        "/discovery/company",
        params={
            "name": "Test Discovery Company",
            "website": "https://example.com",
            "industry": "Technology",
            "country": "India",
            "city": "Mumbai",
            "source": "Test",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["version"] == "1.0.9"

    assert data["company"] == "Test Discovery Company"
    assert data["website"] == "https://example.com"
    assert data["industry"] == "Technology"
    assert data["country"] == "India"
    assert data["city"] == "Mumbai"

    assert "company_id" in data
    assert data["company_id"] is not None


# ---------------------------------------------------------
# DISCOVER DUPLICATE COMPANY
# ---------------------------------------------------------

def test_discover_duplicate_company():
    first_response = client.post(
        "/discovery/company",
        params={
            "name": "Duplicate Company",
            "website": "https://duplicate.example.com",
        },
    )

    assert first_response.status_code == 200

    first_data = first_response.json()

    second_response = client.post(
        "/discovery/company",
        params={
            "name": "Duplicate Company",
            "website": "https://duplicate.example.com",
        },
    )

    assert second_response.status_code == 200

    second_data = second_response.json()

    assert (
        first_data["company_id"]
        == second_data["company_id"]
    )


# ---------------------------------------------------------
# DISCOVER COMPANY - REQUIRED NAME
# ---------------------------------------------------------

def test_discover_company_requires_name():
    response = client.post(
        "/discovery/company"
    )

    assert response.status_code == 422


# ---------------------------------------------------------
# DISCOVER AND PREPARE
# ---------------------------------------------------------

def test_discover_and_prepare_company():
    response = client.post(
        "/discovery/company/prepare",
        params={
            "name": "Prepared Discovery Company",
            "website": "https://prepared.example.com",
            "industry": "Fintech",
            "country": "India",
            "city": "Bangalore",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["company"] == "Prepared Discovery Company"

    assert data["scan_status"] == "Pending"

    assert (
        data["message"]
        == "Company discovered and prepared for scanning."
    )


# ---------------------------------------------------------
# GET COMPANY
# ---------------------------------------------------------

def test_get_company():
    create_response = client.post(
        "/discovery/company",
        params={
            "name": "Company Profile Test",
            "website": "https://profile.example.com",
            "industry": "Banking",
            "country": "India",
            "city": "Delhi",
        },
    )

    assert create_response.status_code == 200

    company_id = (
        create_response.json()["company_id"]
    )

    response = client.get(
        f"/discovery/company/{company_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["company"]["id"] == company_id
    assert (
        data["company"]["name"]
        == "Company Profile Test"
    )
    assert (
        data["company"]["industry"]
        == "Banking"
    )


# ---------------------------------------------------------
# GET COMPANY NOT FOUND
# ---------------------------------------------------------

def test_get_company_not_found():
    response = client.get(
        "/discovery/company/999999"
    )

    assert response.status_code == 404


# ---------------------------------------------------------
# GET COMPANY STATUS
# ---------------------------------------------------------

def test_get_company_status():
    create_response = client.post(
        "/discovery/company",
        params={
            "name": "Status Test Company",
        },
    )

    assert create_response.status_code == 200

    company_id = (
        create_response.json()["company_id"]
    )

    response = client.get(
        f"/discovery/company/{company_id}/status"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["company_id"] == company_id
    assert (
        data["company"]
        == "Status Test Company"
    )

    assert "scan_status" in data
    assert "last_scan" in data


# ---------------------------------------------------------
# COMPANY STATUS NOT FOUND
# ---------------------------------------------------------

def test_company_status_not_found():
    response = client.get(
        "/discovery/company/999999/status"
    )

    assert response.status_code == 404


# ---------------------------------------------------------
# SCAN COMPANY NOT FOUND
# ---------------------------------------------------------

def test_scan_company_not_found():
    response = client.post(
        "/discovery/company/999999/scan"
    )

    assert response.status_code == 404


# ---------------------------------------------------------
# DISCOVER AND SCAN
# ---------------------------------------------------------

def test_discover_and_scan_company():
    response = client.post(
        "/discovery/company/discover-and-scan",
        params={
            "name": "Full Scan Test Company",
            "website": "https://scan.example.com",
            "industry": "Technology",
            "country": "India",
            "city": "Mumbai",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["version"] == "1.0.9"

    assert "company" in data
    assert "website" in data
    assert "linkedin" in data

    assert (
        data["company"]["name"]
        == "Full Scan Test Company"
    )

    assert (
        data["company"]["scan_status"]
        == "Completed"
    )


# ---------------------------------------------------------
# SCAN EXISTING COMPANY
# ---------------------------------------------------------

def test_scan_existing_company():
    create_response = client.post(
        "/discovery/company",
        params={
            "name": "Existing Scan Company",
            "website": "https://existing.example.com",
        },
    )

    assert create_response.status_code == 200

    company_id = (
        create_response.json()["company_id"]
    )

    scan_response = client.post(
        f"/discovery/company/{company_id}/scan",
    )

    assert scan_response.status_code == 200

    data = scan_response.json()

    assert data["success"] is True
    assert data["company"]["id"] == company_id
    assert (
        data["company"]["scan_status"]
        == "Completed"
    )

    assert "website" in data
    assert "linkedin" in data


# ---------------------------------------------------------
# DISCOVER AND SCAN WITH LINKEDIN
# ---------------------------------------------------------

def test_discover_and_scan_with_linkedin():
    response = client.post(
        "/discovery/company/discover-and-scan",
        params={
            "name": "LinkedIn Scan Company",
            "website": "https://linkedin.example.com",
            "linkedin_url": (
                "https://www.linkedin.com/company/"
                "linkedin-scan-company"
            ),
            "linkedin_provider": "TestProvider",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True

    assert (
        data["company"]["name"]
        == "LinkedIn Scan Company"
    )

    assert data["linkedin"] is not None


# ---------------------------------------------------------
# COMPANY PREPARATION LIFECYCLE
# ---------------------------------------------------------

def test_company_preparation_lifecycle():
    response = client.post(
        "/discovery/company/prepare",
        params={
            "name": "Lifecycle Company",
        },
    )

    assert response.status_code == 200

    company_id = (
        response.json()["company_id"]
    )

    status_response = client.get(
        f"/discovery/company/{company_id}/status"
    )

    assert status_response.status_code == 200

    status_data = status_response.json()

    assert (
        status_data["scan_status"]
        == "Pending"
    )

    scan_response = client.post(
        f"/discovery/company/{company_id}/scan"
    )

    assert scan_response.status_code == 200

    final_status_response = client.get(
        f"/discovery/company/{company_id}/status"
    )

    assert (
        final_status_response.status_code
        == 200
    )

    final_status = (
        final_status_response.json()
    )

    assert (
        final_status["scan_status"]
        == "Completed"
    )