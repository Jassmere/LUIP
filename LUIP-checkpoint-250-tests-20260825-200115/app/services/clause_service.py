from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.clause import Clause


class ClauseService:
    """
    Enterprise service layer for Clause Intelligence.

    All business logic for clause retrieval and analytics
    belongs here, keeping routers clean.
    """

    @staticmethod
    def list_clauses(db: Session):
        return (
            db.query(Clause)
            .order_by(Clause.risk_score.desc())
            .all()
        )

    @staticmethod
    def get_clause(
        db: Session,
        clause_id: int,
    ):
        return (
            db.query(Clause)
            .filter(Clause.id == clause_id)
            .first()
        )

    @staticmethod
    def get_document_clauses(
        db: Session,
        document_id: int,
    ):
        return (
            db.query(Clause)
            .filter(
                Clause.document_id == document_id
            )
            .order_by(
                Clause.risk_score.desc()
            )
            .all()
        )

    @staticmethod
    def get_high_risk_clauses(
        db: Session,
    ):
        return (
            db.query(Clause)
            .filter(
                Clause.risk_level == "High"
            )
            .order_by(
                Clause.risk_score.desc()
            )
            .all()
        )

    @staticmethod
    def get_statistics(
        db: Session,
    ):
        total = db.query(Clause).count()

        high = (
            db.query(Clause)
            .filter(
                Clause.risk_level == "High"
            )
            .count()
        )

        medium = (
            db.query(Clause)
            .filter(
                Clause.risk_level == "Medium"
            )
            .count()
        )

        low = (
            db.query(Clause)
            .filter(
                Clause.risk_level == "Low"
            )
            .count()
        )

        average = (
            db.query(
                func.avg(Clause.risk_score)
            ).scalar()
            or 0
        )

        return {
            "total_clauses": total,
            "high_risk": high,
            "medium_risk": medium,
            "low_risk": low,
            "average_risk_score": round(
                average,
                2,
            ),
        }