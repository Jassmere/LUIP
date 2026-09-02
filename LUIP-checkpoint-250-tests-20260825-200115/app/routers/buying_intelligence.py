from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.buying_intelligence_service import (
    BuyingIntelligenceService,
)
from app.services.next_best_action_service import (
    NextBestActionService,
)


router = APIRouter(
    prefix="/buying-intelligence",
    tags=["Buying Intelligence"],
)


# ---------------------------------------------------------
# LIST ALL COMPANIES
# ---------------------------------------------------------

@router.get("/companies")
def list_companies(
    db: Session = Depends(get_db),
):
    return BuyingIntelligenceService.get_all_companies(
        db,
    )


# ---------------------------------------------------------
# COMPANY DETAILS
# ---------------------------------------------------------

@router.get("/company/{company_id}")
def company_details(
    company_id: int,
    db: Session = Depends(get_db),
):
    return BuyingIntelligenceService.get_company(
        company_id,
        db,
    )


# ---------------------------------------------------------
# TOP BUYING TARGETS
# ---------------------------------------------------------

@router.get("/top-targets")
def top_targets(
    db: Session = Depends(get_db),
):
    targets = (
        BuyingIntelligenceService.get_top_buying_targets(
            db,
        )
    )

    results = []

    for target in targets:

        # -------------------------------------------------
        # Support dictionary responses
        # -------------------------------------------------

        if isinstance(target, dict):

            company_id = target.get(
                "company_id",
            )

            company_name = target.get(
                "company",
                target.get(
                    "company_name",
                    "Unknown Company",
                ),
            )

            score = target.get(
                "score",
                target.get(
                    "buying_score",
                    target.get(
                        "buying_intent_score",
                        0,
                    ),
                ),
            )

            confidence = target.get(
                "confidence",
                0,
            )

        # -------------------------------------------------
        # Support ORM/object responses
        # -------------------------------------------------

        else:

            company_id = getattr(
                target,
                "company_id",
                None,
            )

            company_name = getattr(
                target,
                "company",
                "Unknown Company",
            )

            score = getattr(
                target,
                "score",
                getattr(
                    target,
                    "buying_score",
                    getattr(
                        target,
                        "buying_intent_score",
                        0,
                    ),
                ),
            )

            confidence = getattr(
                target,
                "confidence",
                0,
            )

        # -------------------------------------------------
        # Normalize score
        # -------------------------------------------------

        try:
            score = float(score or 0)

        except (TypeError, ValueError):
            score = 0.0

        # -------------------------------------------------
        # Normalize confidence
        # -------------------------------------------------

        try:
            confidence = float(
                confidence or 0
            )

        except (TypeError, ValueError):
            confidence = 0.0

        confidence = min(
            max(confidence, 0.0),
            100.0,
        )

        # -------------------------------------------------
        # Generate Next Best Action
        # -------------------------------------------------

        recommendation = (
            NextBestActionService.generate(
                company_name=company_name,
                score=score,
                lbit_confidence=confidence,
            )
        )

        # -------------------------------------------------
        # Persist Next Best Action
        # -------------------------------------------------

        persisted_action = None

        if company_id is not None:

            persisted_action = (
                NextBestActionService.create_action(
                    db=db,
                    company_id=company_id,
                    score=score,
                    lbit_confidence=confidence,
                )
            )

        # -------------------------------------------------
        # Build result
        # -------------------------------------------------

        if isinstance(target, dict):

            result = dict(target)

        else:

            result = {
                "company_id": company_id,
                "company": company_name,
                "score": score,
                "confidence": confidence,
            }

        # -------------------------------------------------
        # Add normalized score
        # -------------------------------------------------

        result["score"] = score

        # -------------------------------------------------
        # Add generated recommendation
        # -------------------------------------------------

        result["next_best_action"] = recommendation

        # -------------------------------------------------
        # Add persistence metadata
        # -------------------------------------------------

        if persisted_action is not None:

            result["next_best_action_id"] = (
                persisted_action.id
            )

            result["next_best_action_status"] = (
                persisted_action.status
            )

        else:

            result["next_best_action_id"] = None

            result["next_best_action_status"] = (
                "Not persisted"
            )

        results.append(result)

    return results