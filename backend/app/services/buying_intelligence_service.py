from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.company_score import CompanyScore
from app.models.buying_activity import BuyingActivity


class BuyingIntelligenceService:

    HIGH_PRIORITY = 80
    MEDIUM_PRIORITY = 50

    @staticmethod
    def calculate_company_score(
        db: Session,
        company_id: int,
    ):

        activities = (
            db.query(BuyingActivity)
            .filter(
                BuyingActivity.company_id == company_id
            )
            .all()
        )

        if not activities:
            return None

        total_score = sum(
            activity.buying_score
            for activity in activities
        )

        average_confidence = (
            sum(
                activity.confidence
                for activity in activities
            )
            / len(activities)
        )

        if total_score >= BuyingIntelligenceService.HIGH_PRIORITY:

            priority = "High"

        elif total_score >= BuyingIntelligenceService.MEDIUM_PRIORITY:

            priority = "Medium"

        else:

            priority = "Low"

        company_score = (
            db.query(CompanyScore)
            .filter(
                CompanyScore.company_id == company_id
            )
            .first()
        )

        if company_score is None:

            company_score = CompanyScore(
                company_id=company_id,
            )

            db.add(company_score)

        company_score.buying_intent_score = total_score
        company_score.confidence = average_confidence
        company_score.priority = priority

        db.commit()

        db.refresh(company_score)

        return company_score