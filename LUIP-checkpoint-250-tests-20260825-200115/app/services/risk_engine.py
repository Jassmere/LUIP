def calculate_risk(text):

    score = 0

    if "unlimited liability" in text.lower():
        score += 40

    if "sole discretion" in text.lower():
        score += 25

    if "terminate immediately" in text.lower():
        score += 20

    if "without notice" in text.lower():
        score += 15

    if score >= 60:
        level = "High"
    elif score >= 30:
        level = "Medium"
    else:
        level = "Low"

    return score, level