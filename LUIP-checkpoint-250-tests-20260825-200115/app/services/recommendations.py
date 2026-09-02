def recommendation(score):

    if score >= 60:
        return "High legal risk. Review immediately."

    if score >= 30:
        return "Review recommended before signing."

    return "No significant legal concerns detected."