from datetime import datetime

from sqlalchemy.orm import Session

from app.models.next_best_action import NextBestAction


class NextBestActionService:
    """
    LUIP Next Best Action Engine

    Converts a company's buying-intent score
    into an actionable sales recommendation.

    Version: 1.1.0
    """

    VERSION = "1.1.0"

    @staticmethod
    def get_action(score: float):
        """
        Convert buying-intent score into
        a recommended sales action.
        """

        score = float(score or 0)

        if score >= 95:
            return {
                "priority": "Critical",
                "action": "Call immediately",
                "sla": "Within 1 hour",
                "recommended_within_hours": 1,
                "reason": "Immediate buying intent detected",
            }

        if score >= 85:
            return {
                "priority": "High",
                "action": "Book product demonstration",
                "sla": "Within 4 hours",
                "recommended_within_hours": 4,
                "reason": "High probability opportunity",
            }

        if score >= 70:
            return {
                "priority": "Medium",
                "action": "Send personalised email",
                "sla": "Within 24 hours",
                "recommended_within_hours": 24,
                "reason": "Qualified prospect",
            }

        if score >= 50:
            return {
                "priority": "Low",
                "action": "Add to nurture campaign",
                "sla": "Within 72 hours",
                "recommended_within_hours": 72,
                "reason": "Monitor engagement",
            }

        return {
            "priority": "Cold",
            "action": "Continue monitoring",
            "sla": "No immediate action",
            "recommended_within_hours": 168,
            "reason": "Insufficient buying signals",
        }

    @staticmethod
    def generate(
        company_name: str,
        score: float,
    ):
        """
        Generate an in-memory Next Best Action
        recommendation.
        """

        recommendation = (
            NextBestActionService.get_action(score)
        )

        return {
            "company": company_name,
            "score": float(score or 0),
            "generated_at": datetime.utcnow(),
            **recommendation,
        }

    @staticmethod
    def create_action(
        db: Session,
        company_id: int,
        score: float,
        ai_reasoning: str | None = None,
    ):
        """
        Create or refresh the pending Next Best Action
        for a company.

        Existing completed actions are preserved.
        """

        recommendation = (
            NextBestActionService.get_action(score)
        )

        existing = (
            db.query(NextBestAction)
            .filter(
                NextBestAction.company_id == company_id,
                NextBestAction.status == "Pending",
            )
            .order_by(
                NextBestAction.created_at.desc()
            )
            .first()
        )

        if existing:

            existing.action_type = (
                recommendation["action"]
            )

            existing.priority = (
                recommendation["priority"]
            )

            existing.recommended_within_hours = (
                recommendation[
                    "recommended_within_hours"
                ]
            )

            existing.explanation = (
                recommendation["reason"]
            )

            existing.ai_reasoning = ai_reasoning

            db.commit()
            db.refresh(existing)

            return existing

        action = NextBestAction(
            company_id=company_id,
            action_type=recommendation["action"],
            priority=recommendation["priority"],
            recommended_within_hours=(
                recommendation[
                    "recommended_within_hours"
                ]
            ),
            explanation=recommendation["reason"],
            ai_reasoning=ai_reasoning,
            status="Pending",
            created_at=datetime.utcnow(),
        )

        db.add(action)
        db.commit()
        db.refresh(action)

        return action