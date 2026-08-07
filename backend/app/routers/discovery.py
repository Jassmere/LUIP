from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.discovery_service import DiscoveryService

router = APIRouter(
    prefix="/discovery",
    tags=["Discovery"],
)


@router.post("/company")
def discover_company(
    name: str,
    website: str = "",
    industry: str = "",
    country: str = "",
    city: str = "",
    db: Session = Depends(get_db),
):

    company = DiscoveryService.discover_company(
        db=db,
        name=name,
        website=website,
        industry=industry,
        country=country,
        city=city,
        source="Manual",
    )

    return {
        "status": "success",
        "company_id": company.id,
        "company": company.name,
    }