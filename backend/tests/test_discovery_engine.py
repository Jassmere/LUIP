from datetime import datetime
from unittest.mock import patch

from app.discovery.company_discovery import CompanyDiscovery
from app.discovery.discovery_engine import DiscoveryEngine


class FakeCompany:
    def __init__(self):
        self.id = 101
        self.name = "Test Company"
        self.website = "https://testcompany.com"
        self.linkedin_url = (
            "https://www.linkedin.com/company/test-company"
        )
        self.industry = "Technology"
        self.country = "India"
        self.city = "Mumbai"
        self.discovered_from = "Test"
        self.scan_status = "Pending"
        self.last_scan = None


class FakeQuery:
    def __init__(self, company):
        self.company = company

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.company


class FakeDB:
    def __init__(self):
        self.company = FakeCompany()
        self.added = []
        self.commit_count = 0
        self.refresh_count = 0

    def query(self, model):
        return FakeQuery(self.company)

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commit_count += 1

    def refresh(self, obj):
        self.refresh_count += 1


# ---------------------------------------------------------
# Discovery Engine Status
# ---------------------------------------------------------


def test_discovery_engine_status():
    status = DiscoveryEngine.status()

    assert status["engine"] == "LUIP Discovery Engine"
    assert status["version"] == "1.0.9"
    assert status["status"] == "Running"

    assert status["scanners"]["website"] == "Active"
    assert status["scanners"]["linkedin"] == "Active"
    assert status["scanners"]["news"] == "Pending"
    assert status["scanners"]["procurement"] == "Pending"
    assert status["scanners"]["technology"] == "Pending"

    assert status["scan_statuses"]["pending"] == "Pending"
    assert status["scan_statuses"]["scanning"] == "Scanning"
    assert status["scan_statuses"]["completed"] == "Completed"
    assert status["scan_statuses"]["failed"] == "Failed"


# ---------------------------------------------------------
# Company Discovery
# ---------------------------------------------------------


def test_company_discovery_rejects_empty_name():
    db = FakeDB()

    result = CompanyDiscovery.discover(
        db=db,
        name="",
    )

    assert result is None


def test_company_discovery_rejects_missing_name():
    db = FakeDB()

    result = CompanyDiscovery.discover(
        db=db,
        name=None,
    )

    assert result is None


# ---------------------------------------------------------
# Scan Lifecycle
# ---------------------------------------------------------


def test_prepare_company_for_scan():
    db = FakeDB()
    company = FakeCompany()

    result = DiscoveryEngine.prepare_company_for_scan(
        db=db,
        company=company,
    )

    assert result is company
    assert company.scan_status == "Pending"
    assert db.commit_count == 1
    assert db.refresh_count == 1


def test_start_scan():
    db = FakeDB()
    company = FakeCompany()

    result = DiscoveryEngine.start_scan(
        db=db,
        company=company,
    )

    assert result is company
    assert company.scan_status == "Scanning"
    assert db.commit_count == 1
    assert db.refresh_count == 1


def test_complete_scan():
    db = FakeDB()
    company = FakeCompany()

    result = DiscoveryEngine.complete_scan(
        db=db,
        company=company,
    )

    assert result is company
    assert company.scan_status == "Completed"
    assert isinstance(company.last_scan, datetime)
    assert db.commit_count == 1
    assert db.refresh_count == 1


def test_fail_scan():
    db = FakeDB()
    company = FakeCompany()

    result = DiscoveryEngine.fail_scan(
        db=db,
        company=company,
    )

    assert result is company
    assert company.scan_status == "Failed"
    assert db.commit_count == 1
    assert db.refresh_count == 1


# ---------------------------------------------------------
# None Handling
# ---------------------------------------------------------


def test_prepare_company_handles_none():
    db = FakeDB()

    result = DiscoveryEngine.prepare_company_for_scan(
        db=db,
        company=None,
    )

    assert result is None
    assert db.commit_count == 0


def test_start_scan_handles_none():
    db = FakeDB()

    result = DiscoveryEngine.start_scan(
        db=db,
        company=None,
    )

    assert result is None
    assert db.commit_count == 0


def test_complete_scan_handles_none():
    db = FakeDB()

    result = DiscoveryEngine.complete_scan(
        db=db,
        company=None,
    )

    assert result is None
    assert db.commit_count == 0


def test_fail_scan_handles_none():
    db = FakeDB()

    result = DiscoveryEngine.fail_scan(
        db=db,
        company=None,
    )

    assert result is None
    assert db.commit_count == 0


# ---------------------------------------------------------
# Website Scanner Integration
# ---------------------------------------------------------


def test_scan_website():
    company = FakeCompany()

    expected = {
        "success": True,
        "title": "Test Company",
    }

    with patch(
        "app.discovery.discovery_engine.WebsiteScanner.scan_company",
        return_value=expected,
    ) as scanner:

        result = DiscoveryEngine.scan_website(
            company
        )

    assert result == expected
    scanner.assert_called_once_with(company)


def test_scan_website_handles_none():
    result = DiscoveryEngine.scan_website(
        None
    )

    assert result["success"] is False
    assert result["error"] == "Company is required."


# ---------------------------------------------------------
# LinkedIn Scanner Integration
# ---------------------------------------------------------


def test_scan_linkedin():
    company = FakeCompany()

    expected = {
        "success": True,
        "company": "Test Company",
        "linkedin_url": (
            "https://www.linkedin.com/company/test-company"
        ),
    }

    with patch(
        "app.discovery.discovery_engine.LinkedInScanner.scan_company",
        return_value=expected,
    ) as scanner:

        result = DiscoveryEngine.scan_linkedin(
            company=company
        )

    assert result == expected

    scanner.assert_called_once_with(
        company=company,
        linkedin_url=None,
        provider=None,
        profile_data=None,
    )


def test_scan_linkedin_with_provider_data():
    company = FakeCompany()

    profile_data = {
        "industry": "Legal Technology",
        "employee_count": 250,
    }

    expected = {
        "success": True,
        "company": "Test Company",
        "profile": profile_data,
    }

    with patch(
        "app.discovery.discovery_engine.LinkedInScanner.scan_company",
        return_value=expected,
    ) as scanner:

        result = DiscoveryEngine.scan_linkedin(
            company=company,
            linkedin_url=company.linkedin_url,
            provider="TestProvider",
            profile_data=profile_data,
        )

    assert result == expected

    scanner.assert_called_once_with(
        company=company,
        linkedin_url=company.linkedin_url,
        provider="TestProvider",
        profile_data=profile_data,
    )


def test_scan_linkedin_handles_none():
    result = DiscoveryEngine.scan_linkedin(
        None
    )

    assert result["success"] is False
    assert result["error"] == "Company is required."


# ---------------------------------------------------------
# Full Discovery Scan
# ---------------------------------------------------------


def test_discovery_engine_scan_company():
    db = FakeDB()
    company = FakeCompany()

    website_result = {
        "success": True,
        "title": "Test Company",
    }

    linkedin_result = {
        "success": True,
        "company": "Test Company",
        "company_slug": "test-company",
    }

    with patch(
        "app.discovery.discovery_engine.WebsiteScanner.scan_company",
        return_value=website_result,
    ), patch(
        "app.discovery.discovery_engine.LinkedInScanner.scan_company",
        return_value=linkedin_result,
    ):

        result = DiscoveryEngine.scan_company(
            db=db,
            company=company,
        )

    assert result["company"] is company
    assert result["website"] == website_result
    assert result["linkedin"] == linkedin_result

    assert company.scan_status == "Completed"
    assert company.last_scan is not None


def test_discovery_engine_scan_company_passes_linkedin_data():
    db = FakeDB()
    company = FakeCompany()

    website_result = {
        "success": True,
    }

    linkedin_result = {
        "success": True,
    }

    profile_data = {
        "industry": "Fintech",
        "employee_count": 500,
    }

    with patch(
        "app.discovery.discovery_engine.WebsiteScanner.scan_company",
        return_value=website_result,
    ), patch(
        "app.discovery.discovery_engine.LinkedInScanner.scan_company",
        return_value=linkedin_result,
    ) as linkedin_scanner:

        result = DiscoveryEngine.scan_company(
            db=db,
            company=company,
            linkedin_url=company.linkedin_url,
            linkedin_provider="TestProvider",
            linkedin_profile_data=profile_data,
        )

    assert result["website"] == website_result
    assert result["linkedin"] == linkedin_result

    linkedin_scanner.assert_called_once_with(
        company=company,
        linkedin_url=company.linkedin_url,
        provider="TestProvider",
        profile_data=profile_data,
    )


# ---------------------------------------------------------
# Scanner Failure Handling
# ---------------------------------------------------------


def test_discovery_engine_scan_company_failure():
    db = FakeDB()
    company = FakeCompany()

    with patch(
        "app.discovery.discovery_engine.WebsiteScanner.scan_company",
        side_effect=Exception("Website scanner failure"),
    ):

        try:
            DiscoveryEngine.scan_company(
                db=db,
                company=company,
            )
        except Exception as exc:
            assert str(exc) == "Website scanner failure"
        else:
            assert False, (
                "Expected scanner exception to be raised."
            )

    assert company.scan_status == "Failed"


# ---------------------------------------------------------
# Status
# ---------------------------------------------------------


def test_discovery_engine_status_includes_scanners():
    status = DiscoveryEngine.status()

    assert status["scanners"]["website"] == "Active"
    assert status["scanners"]["linkedin"] == "Active"
    assert status["scanners"]["news"] == "Pending"
    assert status["scanners"]["procurement"] == "Pending"
    assert status["scanners"]["technology"] == "Pending"