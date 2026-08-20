"""
LUIP Company Discovery

Provides the company-level discovery interface used by the
LUIP Discovery Engine.

Version: 1.0.9
"""

from app.services.discovery_service import DiscoveryService


class CompanyDiscovery:
    """
    Company discovery facade.

    This class provides a stable discovery interface for the
    Discovery Engine while keeping database persistence inside
    DiscoveryService.
    """

    VERSION = "1.0.9"

    @staticmethod
    def discover(
        db,
        name,
        website=None,
        industry=None,
        country=None,
        city=None,
        source="Manual",
    ):
        """
        Discover a company and persist it using DiscoveryService.

        Existing companies are returned instead of duplicated.
        """

        if not name:
            return None

        return DiscoveryService.discover_company(
            db=db,
            name=name,
            website=website,
            industry=industry,
            country=country,
            city=city,
            source=source,
        )

    @staticmethod
    def exists(db, name):
        """
        Check whether a company already exists.

        Returns:
            Company instance if found, otherwise None.
        """

        if not name:
            return None

        name = name.strip()

        if not name:
            return None

        from app.models.company import Company

        return (
            db.query(Company)
            .filter(Company.name == name)
            .first()
        )