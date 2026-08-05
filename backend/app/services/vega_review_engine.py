"""
LUIP
Vega AI Review Engine

Coordinates all AI review components and produces
a single structured review for a contract.
"""

from collections import Counter

from app.services.risk_analysis_service import (
    RiskAnalysisService,
)


class VegaReviewEngine:

    @staticmethod
    def review(clauses):

        clause_reviews = []
        recommendations = []
        risk_counter = Counter()

        total_score = 0

        for clause in clauses:

            analysis = RiskAnalysisService.analyze(
                clause["clause_type"]
            )

            risk_level = analysis["risk_level"]

            risk_score = analysis["risk_score"]

            recommendation = analysis["recommendation"]

            clause_reviews.append(
                {
                    "clause_type": clause["clause_type"],
                    "heading": clause["heading"],
                    "risk_level": risk_level,
                    "risk_score": risk_score,
                    "recommendation": recommendation,
                }
            )

            risk_counter[risk_level] += 1
            total_score += risk_score

            if risk_level == "High":
                recommendations.append(recommendation)

        clause_count = len(clause_reviews)

        average_score = (
            total_score / clause_count
            if clause_count
            else 0
        )

        health_score = max(
            0,
            min(100, round(100 - average_score))
        )

        if average_score >= 70:
            overall_risk = "High"
        elif average_score >= 40:
            overall_risk = "Medium"
        else:
            overall_risk = "Low"

        return {

            "overall_risk": overall_risk,

            "contract_health": health_score,

            "total_clauses": clause_count,

            "risk_distribution": dict(risk_counter),

            "recommendations": list(
                dict.fromkeys(recommendations)
            ),

            "clauses": clause_reviews,
        }