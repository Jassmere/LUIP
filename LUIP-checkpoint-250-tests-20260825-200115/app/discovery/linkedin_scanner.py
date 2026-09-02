"""
LUIP LinkedIn Scanner

Structured LinkedIn company intelligence scanner.

This module intentionally does not scrape LinkedIn directly.
It provides a controlled interface for LinkedIn/API-backed
company intelligence that can be connected to an approved
data provider later.

Version: 1.0.9
"""

from urllib.parse import urlparse


class LinkedInScanner:
    """
    LinkedIn company intelligence scanner.

    Current implementation:
        - validates LinkedIn URLs
        - normalizes LinkedIn company URLs
        - accepts provider/API supplied data
        - returns structured discovery intelligence

    Future implementation:
        - connect to an approved LinkedIn/API data provider
        - enrich company information
        - detect relevant organizational signals
    """

    VERSION = "1.0.9"

    LINKEDIN_HOSTS = {
        "linkedin.com",
        "www.linkedin.com",
    }

    @classmethod
    def normalize_url(cls, url):
        """
        Normalize a LinkedIn URL.

        Example:

            linkedin.com/company/example
            ->
            https://linkedin.com/company/example
        """

        if not url:
            return None

        url = url.strip()

        if not url:
            return None

        if not url.startswith(
            ("http://", "https://")
        ):
            url = f"https://{url}"

        parsed = urlparse(url)

        if not parsed.netloc:
            return None

        host = parsed.netloc.lower()

        if host not in cls.LINKEDIN_HOSTS:
            return None

        return url.rstrip("/")

    @classmethod
    def is_valid_url(cls, url):
        """
        Determine whether a URL is a LinkedIn URL.
        """

        normalized = cls.normalize_url(url)

        if not normalized:
            return False

        parsed = urlparse(normalized)

        return (
            parsed.scheme in ("http", "https")
            and parsed.netloc.lower()
            in cls.LINKEDIN_HOSTS
            and parsed.path.startswith("/company/")
        )

    @classmethod
    def extract_company_slug(cls, url):
        """
        Extract the LinkedIn company slug.

        Example:

            https://www.linkedin.com/company/acme
            ->
            acme
        """

        normalized = cls.normalize_url(url)

        if not normalized:
            return None

        parsed = urlparse(normalized)

        path = parsed.path.rstrip("/")

        if not path.startswith("/company/"):
            return None

        slug = path.split(
            "/company/",
            1,
        )[1]

        if not slug:
            return None

        return slug.split("/")[0]

    @classmethod
    def build_result(
        cls,
        company,
        linkedin_url=None,
        provider=None,
        profile_data=None,
    ):
        """
        Build a structured LinkedIn discovery result.

        This method is provider-neutral and does not make any
        external network request.
        """

        company_name = getattr(
            company,
            "name",
            None,
        ) if company is not None else None

        company_id = getattr(
            company,
            "id",
            None,
        ) if company is not None else None

        profile_data = profile_data or {}

        normalized_url = cls.normalize_url(
            linkedin_url
        )

        return {
            "success": bool(normalized_url),
            "company_id": company_id,
            "company": company_name,
            "linkedin_url": normalized_url,
            "company_slug": cls.extract_company_slug(
                normalized_url
            ),
            "provider": provider,
            "profile": profile_data,
            "status": (
                "Available"
                if normalized_url
                else "Unavailable"
            ),
            "error": (
                None
                if normalized_url
                else "Invalid LinkedIn company URL."
            ),
        }

    @classmethod
    def scan_company(
        cls,
        company,
        linkedin_url=None,
        provider=None,
        profile_data=None,
    ):
        """
        Scan a company using supplied LinkedIn/API data.

        No external request is performed.

        If linkedin_url is omitted, the scanner will use the
        company's linkedin_url attribute.
        """

        if company is None:
            return {
                "success": False,
                "company_id": None,
                "company": None,
                "linkedin_url": None,
                "company_slug": None,
                "provider": provider,
                "profile": {},
                "status": "Unavailable",
                "error": "Company is required.",
            }

        if linkedin_url is None:
            linkedin_url = getattr(
                company,
                "linkedin_url",
                None,
            )

        if not linkedin_url:
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
                "linkedin_url": None,
                "company_slug": None,
                "provider": provider,
                "profile": {},
                "status": "Unavailable",
                "error": (
                    "Company has no LinkedIn URL."
                ),
            }

        return cls.build_result(
            company=company,
            linkedin_url=linkedin_url,
            provider=provider,
            profile_data=profile_data,
        )

    @classmethod
    def scan_provider_data(
        cls,
        company,
        linkedin_url,
        provider_data,
        provider=None,
    ):
        """
        Convert provider/API data into the standard LUIP
        LinkedIn discovery format.
        """

        if provider_data is None:
            provider_data = {}

        if not isinstance(
            provider_data,
            dict,
        ):
            return {
                "success": False,
                "company_id": getattr(
                    company,
                    "id",
                    None,
                ) if company else None,
                "company": getattr(
                    company,
                    "name",
                    None,
                ) if company else None,
                "linkedin_url": linkedin_url,
                "company_slug": None,
                "provider": provider,
                "profile": {},
                "status": "Unavailable",
                "error": (
                    "Provider data must be a dictionary."
                ),
            }

        return cls.build_result(
            company=company,
            linkedin_url=linkedin_url,
            provider=provider,
            profile_data=provider_data,
        )

    @classmethod
    def status(cls):
        """
        Return scanner status information.
        """

        return {
            "scanner": "LUIP LinkedIn Scanner",
            "version": cls.VERSION,
            "status": "Ready",
            "external_provider": "Not configured",
            "direct_scraping": False,
        }