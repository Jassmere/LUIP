from datetime import datetime

from app.database import SessionLocal
from app.models.company import Company
from app.services.buying_intelligence_service import (
    BuyingIntelligenceService,
)
from app.services.next_best_action_service import (
    NextBestActionService,
)


def run_scoring():

    print("")
    print("======================================")
    print("LUIP Buying Intent Scoring")
    print("======================================")

    print(
        f"[{datetime.utcnow()}] "
        "Calculating buying scores..."
    )

    db = SessionLocal()

    try:

        companies = (
            db.query(Company)
            .filter(
                Company.active == True
            )
            .order_by(
                Company.id.asc()
            )
            .all()
        )

        print(
            f"Companies found: {len(companies)}"
        )

        processed = 0
        scored = 0
        skipped = 0
        errors = 0

        for company in companies:

            processed += 1

            try:

                score = (
                    BuyingIntelligenceService
                    .calculate_company_score(
                        db,
                        company.id,
                    )
                )

                if score is None:

                    skipped += 1

                    print(
                        f"Skipping {company.name} "
                        f"(no buying activity)"
                    )

                    continue

                scored += 1

                score_value = (
                    score.buying_intent_score or 0
                )

                print(
                    f"Scored: {company.name} "
                    f"| Score: {score_value:.1f} "
                    f"| Confidence: "
                    f"{score.confidence:.1f} "
                    f"| Priority: "
                    f"{score.priority}"
                )

                action = (
                    NextBestActionService
                    .create_action(
                        db,
                        company_id=company.id,
                        score=score_value,
                        ai_reasoning=(
                            f"Buying intent score "
                            f"{score_value:.1f} "
                            f"with confidence "
                            f"{score.confidence:.1f}%."
                        ),
                    )
                )

                if action:

                    print(
                        f"NBA: "
                        f"{action.action_type} "
                        f"| {action.priority} "
                        f"| SLA: "
                        f"{action.recommended_within_hours} "
                        f"hours "
                        f"| Status: "
                        f"{action.status}"
                    )

            except Exception as exc:

                errors += 1

                print(
                    f"ERROR scoring "
                    f"{company.name}: {exc}"
                )

                db.rollback()

        print("")
        print("--------------------------------------")
        print("LUIP Scoring Summary")
        print("--------------------------------------")
        print(
            f"Companies processed : {processed}"
        )
        print(
            f"Companies scored    : {scored}"
        )
        print(
            f"Companies skipped   : {skipped}"
        )
        print(
            f"Errors              : {errors}"
        )
        print("--------------------------------------")

        print("Scoring completed.")

    finally:

        db.close()

    print("")