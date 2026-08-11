from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.buying_intelligence_service import BuyingIntelligenceService
from app.services.next_best_action_service import NextBestActionService


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
    return BuyingIntelligenceService.get_all_companies(db)


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
    targets = BuyingIntelligenceService.get_top_buying_targets(
        db,
    )

    results = []

    for target in targets:

        # -------------------------------------------------
        # Support dictionary responses
        # -------------------------------------------------

        if isinstance(target, dict):

            company_name = target.get(
                "company",
                target.get(
                    "company_name",
                    "Unknown Company",
                ),
            )

            # IMPORTANT:
            # BuyingIntelligenceService returns
            # "buying_intent_score".
            #
            # Keep backwards compatibility with:
            # score
            # buying_score
            # buying_intent_score
            #
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

        # -------------------------------------------------
        # Support ORM/object responses
        # -------------------------------------------------

        else:

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

        # -------------------------------------------------
        # Normalize score
        # -------------------------------------------------

        try:
            score = float(score or 0)

        except (TypeError, ValueError):
            score = 0.0

        # -------------------------------------------------
        # Generate Next Best Action
        # -------------------------------------------------

        recommendation = NextBestActionService.generate(
            company_name=company_name,
            score=score,
        )

        # -------------------------------------------------
        # Build result
        # -------------------------------------------------

        if isinstance(target, dict):

            result = dict(target)

        else:

            result = {
                "company": company_name,
                "score": score,
            }

        # -------------------------------------------------
        # Add normalized score for NBA consistency
        #
        # We retain the original buying_intent_score
        # returned by the service while also exposing
        # "score" so downstream components have a
        # consistent field.
        # -------------------------------------------------

        result["score"] = score

        # -------------------------------------------------
        # Add Next Best Action
        # -------------------------------------------------

        result["next_best_action"] = recommendation

        results.append(result)

    return results