"""
LUIP Website Scanner

Performs lightweight website discovery for a company.

The scanner is intentionally independent from the database layer.
It collects website metadata and returns structured information
that can later be converted into LUIP/LBIT discovery signals.

Version: 1.0.9
"""

import re
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse


class WebsiteScanner:
    """
    Lightweight website intelligence scanner.

    No external Python HTTP dependency is required.
    """

    VERSION = "1.0.9"

    DEFAULT_TIMEOUT = 10

    USER_AGENT = (
        "LUIP-Discovery-Engine/1.0.9 "
        "(Company Intelligence Scanner)"
    )

    @staticmethod
    def normalize_url(url):
        """
        Normalize a website URL.

        Examples:

            example.com
            -> https://example.com

            http://example.com/
            -> http://example.com

            https://example.com/about
            -> https://example.com/about
        """

        if not url:
            return None

        url = url.strip()

        if not url:
            return None

        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        parsed = urlparse(url)

        if not parsed.netloc:
            return None

        return url.rstrip("/")

    @staticmethod
    def is_valid_url(url):
        """
        Determine whether a URL is suitable for scanning.
        """

        normalized = WebsiteScanner.normalize_url(url)

        if not normalized:
            return False

        parsed = urlparse(normalized)

        return bool(
            parsed.scheme in ("http", "https")
            and parsed.netloc
        )

    @staticmethod
    def _clean_text(text):
        """
        Remove HTML tags and normalize whitespace.
        """

        if not text:
            return ""

        text = unescape(text)

        text = re.sub(
            r"<script\b[^>]*>.*?</script>",
            " ",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        text = re.sub(
            r"<style\b[^>]*>.*?</style>",
            " ",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        text = re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @staticmethod
    def _extract_title(html):
        """
        Extract the HTML page title.
        """

        if not html:
            return None

        match = re.search(
            r"<title\b[^>]*>(.*?)</title>",
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if not match:
            return None

        title = unescape(match.group(1))

        title = re.sub(
            r"\s+",
            " ",
            title,
        ).strip()

        return title or None

    @staticmethod
    def _extract_description(html):
        """
        Extract the standard HTML meta description.
        """

        if not html:
            return None

        patterns = [
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
            r'<meta[^>]+content=["\'](.*?)["\'][^>]+name=["\']description["\']',
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                html,
                flags=re.IGNORECASE | re.DOTALL,
            )

            if match:
                description = unescape(match.group(1))

                description = re.sub(
                    r"\s+",
                    " ",
                    description,
                ).strip()

                if description:
                    return description

        return None

    @staticmethod
    def _extract_technology_headers(headers):
        """
        Extract basic technology indicators from HTTP headers.

        This is deliberately lightweight. A dedicated technology
        scanner will be responsible for deeper technology discovery.
        """

        if not headers:
            return {}

        technology = {}

        server = headers.get("Server")

        if server:
            technology["server"] = server

        powered_by = headers.get("X-Powered-By")

        if powered_by:
            technology["powered_by"] = powered_by

        return technology

    @classmethod
    def scan(cls, url):
        """
        Scan a website and return structured discovery data.

        The method never raises ordinary network errors to callers.
        Network failures are returned as structured scan results.
        """

        normalized_url = cls.normalize_url(url)

        if not normalized_url:
            return {
                "success": False,
                "url": url,
                "normalized_url": None,
                "status_code": None,
                "final_url": None,
                "title": None,
                "description": None,
                "text": "",
                "technology": {},
                "error": "Invalid website URL.",
            }

        request = Request(
            normalized_url,
            headers={
                "User-Agent": cls.USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
            },
        )

        try:
            with urlopen(
                request,
                timeout=cls.DEFAULT_TIMEOUT,
            ) as response:

                raw = response.read()

                charset = response.headers.get_content_charset()

                if charset:
                    encoding = charset
                else:
                    encoding = "utf-8"

                try:
                    html = raw.decode(
                        encoding,
                        errors="replace",
                    )
                except LookupError:
                    html = raw.decode(
                        "utf-8",
                        errors="replace",
                    )

                title = cls._extract_title(html)

                description = cls._extract_description(html)

                text = cls._clean_text(html)

                technology = cls._extract_technology_headers(
                    response.headers
                )

                final_url = response.geturl()

                return {
                    "success": True,
                    "url": url,
                    "normalized_url": normalized_url,
                    "status_code": response.status,
                    "final_url": final_url,
                    "title": title,
                    "description": description,
                    "text": text[:10000],
                    "technology": technology,
                    "error": None,
                }

        except HTTPError as exc:
            return {
                "success": False,
                "url": url,
                "normalized_url": normalized_url,
                "status_code": exc.code,
                "final_url": None,
                "title": None,
                "description": None,
                "text": "",
                "technology": {},
                "error": f"HTTP error: {exc.code}",
            }

        except URLError as exc:
            return {
                "success": False,
                "url": url,
                "normalized_url": normalized_url,
                "status_code": None,
                "final_url": None,
                "title": None,
                "description": None,
                "text": "",
                "technology": {},
                "error": f"URL error: {exc.reason}",
            }

        except TimeoutError:
            return {
                "success": False,
                "url": url,
                "normalized_url": normalized_url,
                "status_code": None,
                "final_url": None,
                "title": None,
                "description": None,
                "text": "",
                "technology": {},
                "error": "Website request timed out.",
            }

        except Exception as exc:
            return {
                "success": False,
                "url": url,
                "normalized_url": normalized_url,
                "status_code": None,
                "final_url": None,
                "title": None,
                "description": None,
                "text": "",
                "technology": {},
                "error": f"Unexpected scanner error: {exc}",
            }

    @classmethod
    def scan_company(cls, company):
        """
        Scan a Company model/object.

        The company object is not committed or modified here.
        """

        if company is None:
            return {
                "success": False,
                "error": "Company is required.",
            }

        website = getattr(
            company,
            "website",
            None,
        )

        if not website:
            return {
                "success": False,
                "company_id": getattr(
                    company,
                    "id",
                    None,
                ),
                "company": getattr(
                    company,
                    "name",
                    None,
                ),
                "error": "Company has no website.",
            }

        result = cls.scan(website)

        result["company_id"] = getattr(
            company,
            "id",
            None,
        )

        result["company"] = getattr(
            company,
            "name",
            None,
        )

        return result