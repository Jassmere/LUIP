"""
LUIP Discovery Engine

Central orchestration layer for company discovery.

The Discovery Engine coordinates company discovery and intelligence
scanning while keeping individual scanners modular.

Version: 1.0.9
"""

from datetime import datetime, UTC

from app.discovery.company_discovery import CompanyDiscovery
from app.discovery.linkedin_scanner import LinkedInScanner
from app.discovery.website_scanner import WebsiteScanner

from app.services.discovery_signal_bridge import (
    DiscoverySignalBridge,
)


class DiscoveryEngine:
    """
    Central LUIP discovery orchestration engine.

    Responsibilities:

    1. Discover companies.
    2. Prevent duplicate company creation.
    3. Manage discovery scan lifecycle.
    4. Execute intelligence scanners.
    5. Convert discovery intelligence into buying signals.
    6. Provide structured discovery results.
    """

    VERSION = "1.0.9"

    STATUS_PENDING = "Pending"
    STATUS_SCANNING = "Scanning"
    STATUS_COMPLETED = "Completed"
    STATUS_FAILED = "Failed"

    # ---------------------------------------------------------
    # COMPANY DISCOVERY
    # ---------------------------------------------------------

    @classmethod
    def discover_company(
        cls,
        db,
        name,
        website=None,
        industry=None,
        country=None,
        city=None,
        source="Manual",
    ):
        """
        Discover a company through CompanyDiscovery.
        """

        return CompanyDiscovery.discover(
            db=db,
            name=name,
            website=website,
            industry=industry,
            country=country,
            city=city,
            source=source,
        )

    # ---------------------------------------------------------
    # DISCOVERY PREPARATION
    # ---------------------------------------------------------

    @classmethod
    def prepare_company_for_scan(
        cls,
        db,
        company,
    ):
        """
        Prepare a company for the scanning lifecycle.
        """

        if company is None:
            return None

        company.scan_status = cls.STATUS_PENDING

        db.add(company)
        db.commit()
        db.refresh(company)

        return company

    # ---------------------------------------------------------
    # SCAN LIFECYCLE
    # ---------------------------------------------------------

    @classmethod
    def start_scan(
        cls,
        db,
        company,
    ):
        """
        Mark a company as currently being scanned.
        """

        if company is None:
            return None

        company.scan_status = cls.STATUS_SCANNING

        db.add(company)
        db.commit()
        db.refresh(company)

        return company

    # ---------------------------------------------------------
    # WEBSITE SCANNER
    # ---------------------------------------------------------

    @classmethod
    def scan_website(
        cls,
        company,
    ):
        """
        Execute the Website Scanner.

        The scanner does not modify or commit the company.
        """

        if company is None:
            return {
                "success": False,
                "error": "Company is required.",
            }

        return WebsiteScanner.scan_company(
            company
        )

    # ---------------------------------------------------------
    # LINKEDIN SCANNER
    # ---------------------------------------------------------

    @classmethod
    def scan_linkedin(
        cls,
        company,
        linkedin_url=None,
        provider=None,
        profile_data=None,
    ):
        """
        Execute the LinkedIn Scanner.

        No direct LinkedIn scraping is performed.

        The scanner is provider/API-ready and accepts optional
        structured provider data.
        """

        if company is None:
            return {
                "success": False,
                "error": "Company is required.",
            }

        return LinkedInScanner.scan_company(
            company=company,
            linkedin_url=linkedin_url,
            provider=provider,
            profile_data=profile_data,
        )

    # ---------------------------------------------------------
    # DISCOVERY SIGNAL PROCESSING
    # ---------------------------------------------------------

    @classmethod
    def process_discovery_signals(
        cls,
        db,
        company,
        website_result=None,
        linkedin_result=None,
    ):
        """
        Convert discovery intelligence into LUIP buying signals.

        The Discovery Signal Bridge is responsible for translating
        structured Website and LinkedIn intelligence into the
        existing BuyingSignalService pipeline.
        """

        if company is None:
            return {
                "success": False,
                "error": "Company is required.",
                "signals_created": 0,
                "website": None,
                "linkedin": None,
            }

        return DiscoverySignalBridge.process_discovery(
            db=db,
            company=company,
            website_result=website_result,
            linkedin_result=linkedin_result,
        )

    # ---------------------------------------------------------
    # SCAN COMPLETION
    # ---------------------------------------------------------

    @classmethod
    def complete_scan(
        cls,
        db,
        company,
    ):
        """
        Mark a company scan as completed.
        """

        if company is None:
            return None

        company.scan_status = cls.STATUS_COMPLETED
        company.last_scan = datetime.now(UTC)

        db.add(company)
        db.commit()
        db.refresh(company)

        return company

    # ---------------------------------------------------------
    # SCAN FAILURE
    # ---------------------------------------------------------

    @classmethod
    def fail_scan(
        cls,
        db,
        company,
    ):
        """
        Mark a company scan as failed.
        """

        if company is None:
            return None

        company.scan_status = cls.STATUS_FAILED

        db.add(company)
        db.commit()
        db.refresh(company)

        return company

    # ---------------------------------------------------------
    # DISCOVER + PREPARE
    # ---------------------------------------------------------

    @classmethod
    def discover_and_prepare(
        cls,
        db,
        name,
        website=None,
        industry=None,
        country=None,
        city=None,
        source="Manual",
    ):
        """
        Discover a company and prepare it for scanning.
        """

        company = cls.discover_company(
            db=db,
            name=name,
            website=website,
            industry=industry,
            country=country,
            city=city,
            source=source,
        )

        if company is None:
            return None

        return cls.prepare_company_for_scan(
            db=db,
            company=company,
        )

    # ---------------------------------------------------------
    # FULL DISCOVERY SCAN
    # ---------------------------------------------------------

    @classmethod
    def scan_company(
        cls,
        db,
        company,
        linkedin_url=None,
        linkedin_provider=None,
        linkedin_profile_data=None,
    ):
        """
        Execute the complete discovery scanner pipeline.

        Current scanners:

            1. WebsiteScanner
            2. LinkedInScanner

        Discovery intelligence is then processed through:

            3. DiscoverySignalBridge
            4. BuyingSignalService
            5. LBIT
            6. Buying Intelligence
            7. Next Best Action

        Future scanners:

            8. NewsScanner
            9. ProcurementScanner
            10. TechnologyScanner
        """

        if company is None:
            return None

        try:

            # ---------------------------------------------
            # Start lifecycle
            # ---------------------------------------------

            cls.start_scan(
                db=db,
                company=company,
            )

            # ---------------------------------------------
            # Website intelligence
            # ---------------------------------------------

            website_result = cls.scan_website(
                company=company,
            )

            # ---------------------------------------------
            # LinkedIn intelligence
            # ---------------------------------------------

            linkedin_result = cls.scan_linkedin(
                company=company,
                linkedin_url=linkedin_url,
                provider=linkedin_provider,
                profile_data=linkedin_profile_data,
            )

            # ---------------------------------------------
            # Discovery → Buying Signal Bridge
            # ---------------------------------------------

            discovery_signals = (
                cls.process_discovery_signals(
                    db=db,
                    company=company,
                    website_result=website_result,
                    linkedin_result=linkedin_result,
                )
            )

            # ---------------------------------------------
            # Complete lifecycle
            # ---------------------------------------------

            cls.complete_scan(
                db=db,
                company=company,
            )

            return {
                "company": company,
                "website": website_result,
                "linkedin": linkedin_result,
                "discovery_signals": discovery_signals,
            }

        except Exception:

            cls.fail_scan(
                db=db,
                company=company,
            )

            raise

    # ---------------------------------------------------------
    # DISCOVER + SCAN
    # ---------------------------------------------------------

    @classmethod
    def discover_and_scan(
        cls,
        db,
        name,
        website=None,
        industry=None,
        country=None,
        city=None,
        source="Manual",
        linkedin_url=None,
        linkedin_provider=None,
        linkedin_profile_data=None,
    ):
        """
        Discover a company and execute the complete discovery
        scanner pipeline.
        """

        company = cls.discover_company(
            db=db,
            name=name,
            website=website,
            industry=industry,
            country=country,
            city=city,
            source=source,
        )

        if company is None:
            return None

        return cls.scan_company(
            db=db,
            company=company,
            linkedin_url=linkedin_url,
            linkedin_provider=linkedin_provider,
            linkedin_profile_data=linkedin_profile_data,
        )

    # ---------------------------------------------------------
    # ENGINE STATUS
    # ---------------------------------------------------------

    @classmethod
    def status(cls):
        """
        Return Discovery Engine status information.
        """

        return {
            "engine": "LUIP Discovery Engine",
            "version": cls.VERSION,
            "status": "Running",
            "scanners": {
                "website": "Active",
                "linkedin": "Active",
                "news": "Pending",
                "procurement": "Pending",
                "technology": "Pending",
            },
            "signal_bridge": {
                "status": "Active",
                "version": DiscoverySignalBridge.VERSION,
                "website_signals": "Active",
                "linkedin_signals": "Active",
            },
            "scan_statuses": {
                "pending": cls.STATUS_PENDING,
                "scanning": cls.STATUS_SCANNING,
                "completed": cls.STATUS_COMPLETED,
                "failed": cls.STATUS_FAILED,
            },
        }