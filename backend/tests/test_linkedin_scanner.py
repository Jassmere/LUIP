from app.discovery.linkedin_scanner import LinkedInScanner


class FakeCompany:
    def __init__(self):
        self.id = 101
        self.name = "Test Company"
        self.linkedin_url = (
            "https://www.linkedin.com/company/test-company"
        )


def test_normalize_linkedin_url():
    result = LinkedInScanner.normalize_url(
        "linkedin.com/company/test-company"
    )

    assert result == (
        "https://linkedin.com/company/test-company"
    )


def test_normalize_linkedin_url_with_www():
    result = LinkedInScanner.normalize_url(
        "https://www.linkedin.com/company/test-company/"
    )

    assert result == (
        "https://www.linkedin.com/company/test-company"
    )


def test_reject_non_linkedin_url():
    result = LinkedInScanner.normalize_url(
        "https://example.com/company/test-company"
    )

    assert result is None


def test_valid_linkedin_company_url():
    assert LinkedInScanner.is_valid_url(
        "https://www.linkedin.com/company/test-company"
    )


def test_invalid_linkedin_company_url():
    assert not LinkedInScanner.is_valid_url(
        "https://www.linkedin.com/in/test-person"
    )


def test_extract_company_slug():
    result = LinkedInScanner.extract_company_slug(
        "https://www.linkedin.com/company/test-company"
    )

    assert result == "test-company"


def test_extract_company_slug_invalid_url():
    result = LinkedInScanner.extract_company_slug(
        "https://www.linkedin.com/in/test-person"
    )

    assert result is None


def test_scan_company_without_linkedin_url():
    company = FakeCompany()
    company.linkedin_url = None

    result = LinkedInScanner.scan_company(
        company
    )

    assert result["success"] is False
    assert result["company_id"] == 101
    assert result["company"] == "Test Company"
    assert result["error"] == (
        "Company has no LinkedIn URL."
    )


def test_scan_company():
    company = FakeCompany()

    result = LinkedInScanner.scan_company(
        company
    )

    assert result["success"] is True
    assert result["company_id"] == 101
    assert result["company"] == "Test Company"
    assert result["linkedin_url"] == (
        "https://www.linkedin.com/company/test-company"
    )
    assert result["company_slug"] == "test-company"
    assert result["status"] == "Available"


def test_scan_company_with_provider_data():
    company = FakeCompany()

    profile_data = {
        "industry": "Legal Technology",
        "employee_count": 250,
        "country": "India",
    }

    result = LinkedInScanner.scan_company(
        company=company,
        provider="TestProvider",
        profile_data=profile_data,
    )

    assert result["success"] is True
    assert result["provider"] == "TestProvider"
    assert result["profile"]["industry"] == (
        "Legal Technology"
    )
    assert result["profile"]["employee_count"] == 250


def test_scan_provider_data():
    company = FakeCompany()

    provider_data = {
        "industry": "Fintech",
        "employee_count": 500,
    }

    result = LinkedInScanner.scan_provider_data(
        company=company,
        linkedin_url=company.linkedin_url,
        provider_data=provider_data,
        provider="TestProvider",
    )

    assert result["success"] is True
    assert result["provider"] == "TestProvider"
    assert result["company_slug"] == "test-company"
    assert result["profile"] == provider_data


def test_scan_provider_data_rejects_invalid_data():
    company = FakeCompany()

    result = LinkedInScanner.scan_provider_data(
        company=company,
        linkedin_url=company.linkedin_url,
        provider_data="invalid",
        provider="TestProvider",
    )

    assert result["success"] is False
    assert result["error"] == (
        "Provider data must be a dictionary."
    )


def test_scan_company_handles_none():
    result = LinkedInScanner.scan_company(
        None
    )

    assert result["success"] is False
    assert result["error"] == (
        "Company is required."
    )


def test_linkedin_scanner_status():
    status = LinkedInScanner.status()

    assert status["scanner"] == (
        "LUIP LinkedIn Scanner"
    )

    assert status["version"] == "1.0.9"
    assert status["status"] == "Ready"
    assert status["external_provider"] == (
        "Not configured"
    )
    assert status["direct_scraping"] is False