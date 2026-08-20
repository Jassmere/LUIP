"""
LUIP Discovery Signal Bridge

Converts structured discovery intelligence into LUIP
buying-intent signals.

The bridge sits between the Discovery Engine and the
Buying Signal / LBIT pipeline.

Pipeline:

    Website / LinkedIn Discovery
              ↓
       Discovery Signal Bridge
              ↓
       BuyingSignalService
              ↓
             LBIT
              ↓
      Buying Intelligence
              ↓
       Next Best Action

Version: 1.0.0
"""

from app.services.buying_signal_service import (
    BuyingSignalService,
)


class DiscoverySignalBridge:
    """
    Convert discovery intelligence into buying signals.

    The bridge does not perform scanning itself.

    It consumes the structured results returned by:
        - WebsiteScanner
        - LinkedInScanner

    and submits qualifying intelligence to the existing
    BuyingSignalService.
    """

    VERSION = "1.0.0"

    # ---------------------------------------------------------
    # Website intelligence
    # ---------------------------------------------------------

    @classmethod
    def website_signals(
        cls,
        db,
        company,
        discovery_result,
    ):
        """
        Convert website discovery intelligence into
        buying-intent signals.

        The current implementation deliberately uses
        conservative signals.

        A website scan alone does NOT automatically mean
        the company is buying.

        Signals are generated only when meaningful
        commercial/legal indicators are detected.
        """

        if company is None:
            return {
                "success": False,
                "error": "Company is required.",
                "signals_created": 0,
                "signals": [],
            }

        if not discovery_result:
            return {
                "success": True,
                "signals_created": 0,
                "signals": [],
            }

        if not discovery_result.get("success"):
            return {
                "success": True,
                "signals_created": 0,
                "signals": [],
                "reason": "Website scan unsuccessful.",
            }

        signals = []

        text_parts = [
            discovery_result.get("title"),
            discovery_result.get("description"),
            discovery_result.get("text"),
        ]

        searchable_text = " ".join(
            part
            for part in text_parts
            if part
        ).lower()

        # -----------------------------------------------------
        # Commercial / legal technology indicators
        # -----------------------------------------------------

        commercial_terms = {
            "contract management": 35,
            "contract lifecycle": 40,
            "legal operations": 30,
            "legal technology": 30,
            "legaltech": 30,
            "clm": 35,
            "contract automation": 40,
            "document automation": 30,
            "legal automation": 35,
            "agreement management": 35,
        }

        matched_terms = []

        for term, score in commercial_terms.items():
            if term in searchable_text:
                matched_terms.append(
                    (term, score)
                )

        for term, score in matched_terms:
            evidence = (
                f"Website intelligence detected the "
                f"commercial/legal technology indicator "
                f"'{term}'."
            )

            result = BuyingSignalService.create_signal(
                db=db,
                company_id=company.id,
                signal_name=(
                    f"Website mentions {term}"
                ),
                signal_category="Website Intelligence",
                source="Website Scanner",
                source_url=(
                    discovery_result.get(
                        "final_url"
                    )
                    or discovery_result.get(
                        "normalized_url"
                    )
                ),
                evidence=evidence,
                score=score,
                confidence=80.0,
            )

            signals.append(result)

        return {
            "success": True,
            "signals_created": len(
                [
                    result
                    for result in signals
                    if result.get("success")
                ]
            ),
            "signals": signals,
        }

    # ---------------------------------------------------------
    # LinkedIn intelligence
    # ---------------------------------------------------------

    @classmethod
    def linkedin_signals(
        cls,
        db,
        company,
        discovery_result,
    ):
        """
        Convert structured LinkedIn provider intelligence
        into buying-intent signals.

        No LinkedIn scraping is performed.

        The method only evaluates provider/API supplied
        structured data.
        """

        if company is None:
            return {
                "success": False,
                "error": "Company is required.",
                "signals_created": 0,
                "signals": [],
            }

        if not discovery_result:
            return {
                "success": True,
                "signals_created": 0,
                "signals": [],
            }

        if not discovery_result.get("success"):
            return {
                "success": True,
                "signals_created": 0,
                "signals": [],
                "reason": "LinkedIn data unavailable.",
            }

        profile = discovery_result.get(
            "profile"
        ) or {}

        if not isinstance(profile, dict):
            return {
                "success": True,
                "signals_created": 0,
                "signals": [],
                "reason": "LinkedIn profile data is not structured.",
            }

        signals = []

        source_url = discovery_result.get(
            "linkedin_url"
        )

        # -----------------------------------------------------
        # Hiring / legal operations indicators
        # -----------------------------------------------------

        hiring_terms = {
            "legal operations": 40,
            "legal ops": 40,
            "contract manager": 35,
            "contract management": 40,
            "legal technology": 35,
            "legaltech": 35,
            "commercial contracts": 35,
            "contracts manager": 35,
        }

        # Convert structured profile data into searchable
        # text without assuming a specific provider schema.

        profile_text = cls._flatten_profile(
            profile
        ).lower()

        for term, score in hiring_terms.items():

            if term not in profile_text:
                continue

            evidence = (
                f"LinkedIn provider intelligence "
                f"detected the indicator '{term}'."
            )

            result = BuyingSignalService.create_signal(
                db=db,
                company_id=company.id,
                signal_name=(
                    f"LinkedIn intelligence: {term}"
                ),
                signal_category="LinkedIn Intelligence",
                source=(
                    discovery_result.get(
                        "provider"
                    )
                    or "LinkedIn Provider"
                ),
                source_url=source_url,
                evidence=evidence,
                score=score,
                confidence=75.0,
            )

            signals.append(result)

        return {
            "success": True,
            "signals_created": len(
                [
                    result
                    for result in signals
                    if result.get("success")
                ]
            ),
            "signals": signals,
        }

    # ---------------------------------------------------------
    # Combined discovery intelligence
    # ---------------------------------------------------------

    @classmethod
    def process_discovery(
        cls,
        db,
        company,
        website_result=None,
        linkedin_result=None,
    ):
        """
        Process all currently supported discovery
        intelligence.

        This is the primary entry point used by the
        Discovery Engine.
        """

        if company is None:
            return {
                "success": False,
                "error": "Company is required.",
                "website": None,
                "linkedin": None,
                "signals_created": 0,
            }

        website = cls.website_signals(
            db=db,
            company=company,
            discovery_result=website_result,
        )

        linkedin = cls.linkedin_signals(
            db=db,
            company=company,
            discovery_result=linkedin_result,
        )

        website_count = website.get(
            "signals_created",
            0,
        )

        linkedin_count = linkedin.get(
            "signals_created",
            0,
        )

        return {
            "success": True,
            "company_id": company.id,
            "company": company.name,
            "website": website,
            "linkedin": linkedin,
            "signals_created": (
                website_count
                + linkedin_count
            ),
        }

    # ---------------------------------------------------------
    # Profile flattening helper
    # ---------------------------------------------------------

    @staticmethod
    def _flatten_profile(
        value,
    ):
        """
        Convert arbitrary provider profile data into a
        searchable string.

        This allows different LinkedIn/API providers to
        supply nested dictionaries/lists without requiring
        a fixed provider schema.
        """

        if value is None:
            return ""

        if isinstance(value, dict):

            return " ".join(
                DiscoverySignalBridge._flatten_profile(
                    item
                )
                for item in value.values()
            )

        if isinstance(value, (list, tuple, set)):

            return " ".join(
                DiscoverySignalBridge._flatten_profile(
                    item
                )
                for item in value
            )

        return str(value)

    # ---------------------------------------------------------
    # Status
    # ---------------------------------------------------------

    @classmethod
    def status(cls):
        """
        Return Discovery Signal Bridge status.
        """

        return {
            "bridge": (
                "LUIP Discovery Signal Bridge"
            ),
            "version": cls.VERSION,
            "status": "Ready",
            "website_signals": "Active",
            "linkedin_signals": "Active",
            "direct_linkedin_scraping": False,
        }