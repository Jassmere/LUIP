from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.discovery_service import DiscoveryService

router = APIRouter(
    prefix="/discovery",
    tags=["Company Discovery"],
)


@router.post("/company")
def discover_company(
    name: str,
    website: str | None = None,
    industry: str | None = None,
    country: str | None = None,
    city: str | None = None,
    source: str = "Manual",
    db: Session = Depends(get_db),
):
    company = DiscoveryService.discover_company(
        db=db,
        name=name,
        website=website,
        industry=industry,
        country=country,
        city=city,
        source=source,
    )

    return {
        "success": True,
        "company_id": company.id,
        "company": company.name,
        "website": company.website,
        "industry": company.industry,
        "country": company.country,
        "city": company.city,
        "message": "Company discovered successfully.",
    }


@router.get("/status")
def discovery_status():
    return {
        "engine": "LUIP Discovery Engine",
        "status": "Running",
        "version": "1.0.9",
    }