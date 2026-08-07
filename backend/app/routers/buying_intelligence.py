from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.database import get_db
from app.services.buying_intelligence_service import BuyingIntelligenceService

router = APIRouter(
    prefix="/buying-intelligence",
    tags=["Buying Intelligence"],
)


@router.get("/companies")
def list_companies(
    db: Session = Depends(get_db),
):

    return BuyingIntelligenceService.get_all_companies(db)


@router.get("/company/{company_id}")
def company_details(
    company_id: int,
    db: Session = Depends(get_db),
):

    return BuyingIntelligenceService.get_company(
        company_id,
        db,
    )


@router.get("/top-targets")
def top_targets(
    db: Session = Depends(get_db),
):

    return BuyingIntelligenceService.get_top_buying_targets(
        db,
    )