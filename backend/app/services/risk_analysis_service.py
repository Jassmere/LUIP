class RiskAnalysisService:
    """
    AI Risk Intelligence Engine

    Determines:
    - Risk Level
    - Risk Score
    - Recommendation
    """

    HIGH_RISK = {
        "Indemnity",
        "Limitation of Liability",
        "Intellectual Property",
        "Termination",
    }

    MEDIUM_RISK = {
        "Payment",
        "Force Majeure",
        "Confidentiality",
    }

    LOW_RISK = {
        "Definitions",
        "Notices",
        "General",
        "Miscellaneous",
        "Governing Law",
    }

    @staticmethod
    def analyze(clause_type: str):

        if clause_type in RiskAnalysisService.HIGH_RISK:

            return {
                "risk_level": "High",
                "risk_score": 90,
                "recommendation":
                    "Legal review strongly recommended. "
                    "This clause may expose the organization "
                    "to significant legal risk.",
            }

        if clause_type in RiskAnalysisService.MEDIUM_RISK:

            return {
                "risk_level": "Medium",
                "risk_score": 55,
                "recommendation":
                    "Review this clause carefully to ensure "
                    "it aligns with company policy.",
            }

        return {
            "risk_level": "Low",
            "risk_score": 20,
            "recommendation":
                "No significant legal concerns detected.",
        }