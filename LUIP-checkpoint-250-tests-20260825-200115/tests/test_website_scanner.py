from io import BytesIO
from unittest.mock import patch

from app.discovery.website_scanner import WebsiteScanner


class FakeHeaders:
    def get_content_charset(self):
        return "utf-8"

    def get(self, name, default=None):
        values = {
            "Server": "TestServer",
            "X-Powered-By": "TestFramework",
        }

        return values.get(name, default)


class FakeResponse:
    status = 200
    headers = FakeHeaders()

    def __init__(self):
        self.data = (
            b"""
            <html>
                <head>
                    <title>Test Company</title>
                    <meta name="description"
                          content="A test company website.">
                    <style>body { display: none; }</style>
                    <script>alert('test');</script>
                </head>
                <body>
                    <h1>Test Company</h1>
                    <p>Legal technology company.</p>
                </body>
            </html>
            """
        )

    def read(self):
        return self.data

    def geturl(self):
        return "https://testcompany.com"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class FakeCompany:
    id = 100
    name = "Test Company"
    website = "https://testcompany.com"


def test_normalize_url_adds_https():
    result = WebsiteScanner.normalize_url(
        "example.com"
    )

    assert result == "https://example.com"


def test_normalize_url_removes_trailing_slash():
    result = WebsiteScanner.normalize_url(
        "https://example.com/"
    )

    assert result == "https://example.com"


def test_normalize_url_rejects_empty_value():
    assert WebsiteScanner.normalize_url("") is None
    assert WebsiteScanner.normalize_url(None) is None


def test_valid_url():
    assert WebsiteScanner.is_valid_url(
        "https://example.com"
    )

    assert WebsiteScanner.is_valid_url(
        "example.com"
    )


def test_invalid_url():
    assert not WebsiteScanner.is_valid_url(
        ""
    )

    assert not WebsiteScanner.is_valid_url(
        None
    )


def test_extract_title():
    html = "<html><title>Example Company</title></html>"

    result = WebsiteScanner._extract_title(html)

    assert result == "Example Company"


def test_extract_description():
    html = (
        '<meta name="description" '
        'content="Example description">'
    )

    result = WebsiteScanner._extract_description(html)

    assert result == "Example description"


def test_clean_text_removes_scripts_and_html():
    html = """
    <html>
        <script>secret()</script>
        <body>
            <h1>Hello Company</h1>
            <p>Legal technology.</p>
        </body>
    </html>
    """

    result = WebsiteScanner._clean_text(html)

    assert "Hello Company" in result
    assert "Legal technology." in result
    assert "secret()" not in result


@patch(
    "app.discovery.website_scanner.urlopen"
)
def test_scan_success(mock_urlopen):
    mock_urlopen.return_value = FakeResponse()

    result = WebsiteScanner.scan(
        "https://testcompany.com"
    )

    assert result["success"] is True
    assert result["status_code"] == 200
    assert result["title"] == "Test Company"
    assert result["description"] == (
        "A test company website."
    )
    assert "Legal technology company." in result["text"]

    assert result["technology"]["server"] == (
        "TestServer"
    )

    assert result["technology"]["powered_by"] == (
        "TestFramework"
    )


def test_scan_invalid_url():
    result = WebsiteScanner.scan(
        ""
    )

    assert result["success"] is False
    assert result["error"] == (
        "Invalid website URL."
    )


def test_scan_company_without_website():
    company = FakeCompany()
    company.website = None

    result = WebsiteScanner.scan_company(
        company
    )

    assert result["success"] is False
    assert result["company"] == "Test Company"
    assert result["error"] == (
        "Company has no website."
    )


@patch(
    "app.discovery.website_scanner.urlopen"
)
def test_scan_company(mock_urlopen):
    mock_urlopen.return_value = FakeResponse()

    company = FakeCompany()

    result = WebsiteScanner.scan_company(
        company
    )

    assert result["success"] is True
    assert result["company_id"] == 100
    assert result["company"] == "Test Company"
    assert result["title"] == "Test Company"