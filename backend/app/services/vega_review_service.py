from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

from app.models.clause import Clause

from app.services.risk_analysis_service import (
    RiskAnalysisService,
)


engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class VegaReviewService:
    """
    Generates a complete Vega AI legal review.
    """

    @staticmethod
    def review_document(document_id: int):

        db = SessionLocal()

        try:

            clauses = (
                db.query(Clause)
                .filter(
                    Clause.document_id == document_id
                )
                .all()
            )

            clause_data = []

            for clause in clauses:

                clause_data.append({

                    "clause_type": clause.clause_type,

                    "heading": clause.heading,

                    "content": clause.content,

                })

            return VegaReviewService.generate_review(
                clause_data
            )

        finally:

            db.close()

    @staticmethod
    def generate_review(clauses):

        review = {

            "summary": "",

            "red_flags": [],

            "improvements": [],

            "missing": [],

        }

        high_risk = 0

        for clause in clauses:

            risk = RiskAnalysisService.analyze(

                clause["clause_type"]

            )

            if risk["risk_level"] == "High":

                high_risk += 1

                review["red_flags"].append({

                    "clause": clause["heading"],

                    "risk": risk["recommendation"],

                })

            elif risk["risk_level"] == "Medium":

                review["improvements"].append({

                    "clause": clause["heading"],

                    "recommendation": risk["recommendation"],

                })

        required = [

            "Termination",

            "Confidentiality",

            "Limitation of Liability",

            "Governing Law",

            "Dispute Resolution",

        ]

        existing = [

            c["clause_type"]

            for c in clauses

        ]

        for item in required:

            if item not in existing:

                review["missing"].append(item)

        review["summary"] = (

            f"Contract contains {len(clauses)} clauses. "

            f"{high_risk} high-risk issues detected."

        )

        return review