from datetime import datetime


class NextBestActionService:
    """
    LUIP Next Best Action Engine

    Determines the next recommended action
    for every discovered company based on
    buying intent score.
    """

    @staticmethod
    def get_action(score: int):

        if score >= 95:
            return {
                "priority": "Critical",
                "action": "Call immediately",
                "sla": "Within 1 hour",
                "reason": "Immediate buying intent detected",
            }

        if score >= 85:
            return {
                "priority": "High",
                "action": "Book product demonstration",
                "sla": "Within 4 hours",
                "reason": "High probability opportunity",
            }

        if score >= 70:
            return {
                "priority": "Medium",
                "action": "Send personalised email",
                "sla": "Within 24 hours",
                "reason": "Qualified prospect",
            }

        if score >= 50:
            return {
                "priority": "Low",
                "action": "Add to nurture campaign",
                "sla": "Within 72 hours",
                "reason": "Monitor engagement",
            }

        return {
            "priority": "Cold",
            "action": "Continue monitoring",
            "sla": "No immediate action",
            "reason": "Insufficient buying signals",
        }

    @staticmethod
    def generate(company_name: str, score: int):

        recommendation = NextBestActionService.get_action(score)

        return {
            "company": company_name,
            "score": score,
            "generated_at": datetime.utcnow(),
            **recommendation,
        }