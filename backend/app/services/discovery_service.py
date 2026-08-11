from datetime import datetime

from app.models.company import Company


class DiscoveryService:
    """
    LUIP Discovery Service

    Responsible for discovering and storing
    newly identified companies.
    """

    VERSION = "1.0.9"

    @staticmethod
    def discover_company(
        db,
        name,
        website=None,
        industry=None,
        country=None,
        city=None,
        source="Manual",
    ):

        if not name:
            return None

        name = name.strip()

        if website:
            website = website.strip().lower()

        existing = (
            db.query(Company)
            .filter(Company.name == name)
            .first()
        )

        if existing:
            return existing

        company = Company(
            name=name,
            website=website,
            industry=industry,
            country=country,
            city=city,
            discovered_from=source,
            discovery_date=datetime.utcnow(),
        )

        db.add(company)
        db.commit()
        db.refresh(company)

        print(f"✓ Company discovered: {company.name}")

        return company