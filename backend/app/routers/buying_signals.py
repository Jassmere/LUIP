from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.buying_signal_service import BuyingSignalService


router = APIRouter(
    prefix="/buying-signals",
    tags=["Buying Signals"],
)


# ---------------------------------------------------------
# CREATE BUYING SIGNAL
# ---------------------------------------------------------

@router.post("/")
def create_buying_signal(
    company_id: int,
    signal_name: str,
    signal_category: str,
    source: str | None = None,
    source_url: str | None = None,
    evidence: str | None = None,
    score: float = 0.0,
    confidence: float = 100.0,
    db: Session = Depends(get_db),
):
    """
    Ingest a buying-intent signal into LUIP.

    The signal is converted into a buying activity,
    incorporated into the company scoring engine,
    and used to generate the Next Best Action.
    """

    return BuyingSignalService.create_signal(
        db=db,
        company_id=company_id,
        signal_name=signal_name,
        signal_category=signal_category,
        source=source,
        source_url=source_url,
        evidence=evidence,
        score=score,
        confidence=confidence,
    )


# ---------------------------------------------------------
# BUYING SIGNAL ENGINE STATUS
# ---------------------------------------------------------

@router.get("/status")
def buying_signal_status():
    return {
        "engine": "LUIP Buying Signal Ingestion Engine",
        "status": "Running",
        "version": "1.1.1",
    }