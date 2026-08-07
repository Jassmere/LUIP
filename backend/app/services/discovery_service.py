from datetime import datetime

from app.models.company import Company


class DiscoveryService:

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

        return company