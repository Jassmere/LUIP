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
            activity.buying_score or 0
            for activity in activities
        )

        average_confidence = (
            sum(
                activity.confidence or 0
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

    @staticmethod
    def get_all_companies(db: Session):

        companies = (
            db.query(Company)
            .order_by(Company.name.asc())
            .all()
        )

        results = []

        for company in companies:

            score = (
                db.query(CompanyScore)
                .filter(
                    CompanyScore.company_id == company.id
                )
                .first()
            )

            results.append({
                "company_id": company.id,
                "company": company.name,
                "website": company.website,
                "industry": company.industry,
                "country": company.country,
                "city": company.city,
                "buying_intent_score": (
                    score.buying_intent_score
                    if score else 0
                ),
                "confidence": (
                    score.confidence
                    if score else 0
                ),
                "priority": (
                    score.priority
                    if score else "Low"
                ),
            })

        return results

    @staticmethod
    def get_company(
        company_id: int,
        db: Session,
    ):

        company = (
            db.query(Company)
            .filter(
                Company.id == company_id
            )
            .first()
        )

        if company is None:
            return {
                "error": "Company not found"
            }

        score = (
            db.query(CompanyScore)
            .filter(
                CompanyScore.company_id == company_id
            )
            .first()
        )

        activities = (
            db.query(BuyingActivity)
            .filter(
                BuyingActivity.company_id == company_id
            )
            .order_by(
                BuyingActivity.discovered_at.desc()
            )
            .all()
        )

        return {
            "company_id": company.id,
            "company": company.name,
            "website": company.website,
            "industry": company.industry,
            "country": company.country,
            "city": company.city,
            "buying_intent_score": (
                score.buying_intent_score
                if score else 0
            ),
            "confidence": (
                score.confidence
                if score else 0
            ),
            "priority": (
                score.priority
                if score else "Low"
            ),
            "activities": [
                {
                    "id": activity.id,
                    "activity_type": activity.activity_type,
                    "activity_source": activity.activity_source,
                    "title": activity.title,
                    "description": activity.description,
                    "buying_score": activity.buying_score,
                    "confidence": activity.confidence,
                    "discovered_at": activity.discovered_at,
                }
                for activity in activities
            ],
        }

    @staticmethod
    def get_top_buying_targets(
        db: Session,
    ):

        targets = (
            db.query(
                Company,
                CompanyScore,
            )
            .join(
                CompanyScore,
                CompanyScore.company_id == Company.id,
            )
            .order_by(
                CompanyScore.buying_intent_score.desc()
            )
            .all()
        )

        results = []

        for company, score in targets:

            results.append({
                "company_id": company.id,
                "company": company.name,
                "website": company.website,
                "industry": company.industry,
                "country": company.country,
                "city": company.city,
                "buying_intent_score": score.buying_intent_score,
                "confidence": score.confidence,
                "priority": score.priority,
                "last_updated": score.last_updated,
            })

        return results