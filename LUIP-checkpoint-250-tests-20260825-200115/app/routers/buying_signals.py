from fastapi import APIRouter, Depends, HTTPException
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
    payload: dict,
    db: Session = Depends(get_db),
):
    """
    Ingest a buying-intent signal into LUIP.

    Processing pipeline:

        Buying Signal
            ↓
        LBIT Classification
            ↓
        BuyingIntentSignal
            ↓
        BuyingActivity
            ↓
        Company Buying-Intent Score
            ↓
        Next Best Action

    Signals without an established LBIT taxonomy definition
    remain valid LUIP signals and are stored without an
    LBIT classification.
    """

    result = BuyingSignalService.create_signal(
        db=db,
        company_id=payload.get("company_id"),
        signal_name=payload.get("signal_name"),
        signal_category=payload.get("signal_category"),
        source=payload.get("source"),
        source_url=payload.get("source_url"),
        evidence=payload.get("evidence"),
        score=payload.get("score", 0.0),
        confidence=payload.get("confidence", 100.0),
    )

    # -----------------------------------------------------
    # Convert service validation failures into HTTP errors
    # -----------------------------------------------------

    if not result.get("success", False):

        error = result.get(
            "error",
            "Unable to create buying signal.",
        )

        # Invalid company / bad request
        if "not found" in error.lower():
            raise HTTPException(
                status_code=404,
                detail=error,
            )

        raise HTTPException(
            status_code=400,
            detail=error,
        )

    # -----------------------------------------------------
    # Backward-compatible response fields
    #
    # Keep the full v1.3 nested response while also
    # exposing the fields expected by the existing router
    # tests and earlier LUIP API consumers.
    # -----------------------------------------------------

    company_data = result.get(
        "company",
        {},
    )

    signal_data = result.get(
        "signal",
        {},
    )

    lbit_data = result.get(
        "lbit",
        {},
    )

    return {
        # -------------------------------------------------
        # Core response
        # -------------------------------------------------

        "success": True,

        "version": result.get(
            "version",
            BuyingSignalService.VERSION,
        ),

        # -------------------------------------------------
        # Backward-compatible top-level fields
        # -------------------------------------------------

        "company_id": company_data.get("id"),

        "company": company_data,

        "signal_id": signal_data.get("id"),

        "signal_name": signal_data.get(
            "signal_name"
        ),

        "signal_category": signal_data.get(
            "signal_category"
        ),

        "source": signal_data.get(
            "source"
        ),

        "source_url": signal_data.get(
            "source_url"
        ),

        "evidence": signal_data.get(
            "evidence"
        ),

        "score": signal_data.get(
            "score"
        ),

        "confidence": signal_data.get(
            "confidence"
        ),

        # -------------------------------------------------
        # LBIT compatibility fields
        # -------------------------------------------------

        "lbit_level": lbit_data.get(
            "level"
        ),

        "lbit_category": lbit_data.get(
            "category"
        ),

        "lbit_score": lbit_data.get(
            "score"
        ),

        "lbit_confidence": lbit_data.get(
            "confidence"
        ),

        # -------------------------------------------------
        # Full v1.3 objects
        # -------------------------------------------------

        "signal": signal_data,

        "lbit": lbit_data,

        "company_score": result.get(
            "company_score"
        ),

        "next_best_action": result.get(
            "next_best_action"
        ),

        "buying_activity": result.get(
            "buying_activity"
        ),
    }


# ---------------------------------------------------------
# BUYING SIGNAL ENGINE STATUS
# ---------------------------------------------------------

@router.get("/status")
def buying_signal_status():
    """
    Return the current Buying Signal Ingestion Engine
    status.
    """

    return {
        "service": "LUIP Buying Signal Service",
        "engine": "LUIP Buying Signal Ingestion Engine",
        "status": "Running",
        "version": BuyingSignalService.VERSION,
    }