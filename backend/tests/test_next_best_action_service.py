from app.services.next_best_action_service import (
    NextBestActionService,
)


# =========================================================
# SCORE NORMALISATION
# =========================================================


def test_score_normalisation_preserves_valid_score():
    score = NextBestActionService._normalise_score(95)

    assert score == 95.0


def test_score_normalisation_converts_string_score():
    score = NextBestActionService._normalise_score("85")

    assert score == 85.0


def test_score_normalisation_handles_none():
    score = NextBestActionService._normalise_score(None)

    assert score == 0.0


def test_score_normalisation_handles_invalid_value():
    score = NextBestActionService._normalise_score(
        "invalid"
    )

    assert score == 0.0


def test_score_normalisation_clamps_negative_score():
    score = NextBestActionService._normalise_score(-25)

    assert score == 0.0


def test_score_normalisation_clamps_score_above_100():
    score = NextBestActionService._normalise_score(150)

    assert score == 100.0


# =========================================================
# SCORE → NEXT BEST ACTION
# =========================================================


def test_critical_score_returns_immediate_call():
    action = NextBestActionService.get_action(95)

    assert action["priority"] == "Critical"

    assert action["action"] == (
        "Call immediately"
    )

    assert action["recommended_within_hours"] == 1


def test_high_score_returns_product_demo():
    action = NextBestActionService.get_action(85)

    assert action["priority"] == "High"

    assert action["action"] == (
        "Book product demonstration"
    )

    assert action["recommended_within_hours"] == 4


def test_medium_score_returns_personalised_email():
    action = NextBestActionService.get_action(70)

    assert action["priority"] == "Medium"

    assert action["action"] == (
        "Send personalised email"
    )

    assert action["recommended_within_hours"] == 24


def test_low_score_returns_nurture_campaign():
    action = NextBestActionService.get_action(50)

    assert action["priority"] == "Low"

    assert action["action"] == (
        "Add to nurture campaign"
    )

    assert action["recommended_within_hours"] == 72


def test_cold_score_returns_monitoring():
    action = NextBestActionService.get_action(49)

    assert action["priority"] == "Cold"

    assert action["action"] == (
        "Continue monitoring"
    )

    assert action["recommended_within_hours"] == 168


# =========================================================
# BOUNDARY TESTS
# =========================================================


def test_score_100_returns_critical():
    action = NextBestActionService.get_action(100)

    assert action["priority"] == "Critical"


def test_score_zero_returns_cold():
    action = NextBestActionService.get_action(0)

    assert action["priority"] == "Cold"


def test_score_94_returns_high():
    action = NextBestActionService.get_action(94)

    assert action["priority"] == "High"


def test_score_84_returns_medium():
    action = NextBestActionService.get_action(84)

    assert action["priority"] == "Medium"


def test_score_69_returns_low():
    action = NextBestActionService.get_action(69)

    assert action["priority"] == "Low"


# =========================================================
# IN-MEMORY GENERATION
# =========================================================


def test_generate_returns_company_and_score():
    result = NextBestActionService.generate(
        company_name="Test Company",
        score=95,
    )

    assert result["company"] == "Test Company"

    assert result["score"] == 95.0

    assert result["priority"] == "Critical"

    assert result["action"] == (
        "Call immediately"
    )

    assert result["recommended_within_hours"] == 1

    assert result["generated_at"] is not None


def test_generate_normalises_score():
    result = NextBestActionService.generate(
        company_name="Test Company",
        score=150,
    )

    assert result["score"] == 100.0

    assert result["priority"] == "Critical"