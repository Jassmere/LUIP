import pytest

from app.services.lbit_service import (
    LBITClassification,
    LBITService,
)


class TestLBITService:
    """
    Automated tests for the LUIP Legal Buying Intent Taxonomy.

    Current verified taxonomy coverage:
        Level 5 — Immediate Buying Intent
    """

    # ---------------------------------------------------------
    # LEVEL 5 SIGNALS
    # ---------------------------------------------------------

    @pytest.mark.parametrize(
        "signal_name",
        [
            "requested_demo",
            "pricing_page_repeat_visit",
            "feature_request_response",
            "clm_rfp",
            "clm_rfq",
            "proposal_request",
        ],
    )
    def test_level_5_signal_classification(
        self,
        signal_name,
    ):
        result = LBITService.classify(
            signal_name=signal_name,
            score=95.0,
            confidence=100.0,
        )

        assert isinstance(
            result,
            LBITClassification,
        )

        assert result.level == 5

        assert (
            result.category
            == "Immediate Buying Intent"
        )

        assert result.score == 95.0

        assert result.confidence == 100.0

        assert result.signal_name == signal_name

    # ---------------------------------------------------------
    # LEVEL 5 LOWER SCORE BOUNDARY
    # ---------------------------------------------------------

    def test_level_5_accepts_score_of_90(self):
        result = LBITService.classify(
            signal_name="requested_demo",
            score=90.0,
            confidence=100.0,
        )

        assert result.level == 5
        assert result.score == 90.0

    # ---------------------------------------------------------
    # LEVEL 5 UPPER SCORE BOUNDARY
    # ---------------------------------------------------------

    def test_level_5_accepts_score_of_100(self):
        result = LBITService.classify(
            signal_name="requested_demo",
            score=100.0,
            confidence=100.0,
        )

        assert result.level == 5
        assert result.score == 100.0

    # ---------------------------------------------------------
    # SCORE BELOW LEVEL 5
    # ---------------------------------------------------------

    def test_level_5_rejects_score_below_90(self):
        with pytest.raises(ValueError):
            LBITService.classify(
                signal_name="requested_demo",
                score=89.99,
                confidence=100.0,
            )

    # ---------------------------------------------------------
    # SCORE ABOVE LEVEL 5
    # ---------------------------------------------------------

    def test_level_5_rejects_score_above_100(self):
        with pytest.raises(ValueError):
            LBITService.classify(
                signal_name="requested_demo",
                score=100.01,
                confidence=100.0,
            )

    # ---------------------------------------------------------
    # SIGNAL NORMALIZATION — SPACES
    # ---------------------------------------------------------

    def test_signal_name_normalizes_spaces(self):
        result = LBITService.classify(
            signal_name="Requested Demo",
            score=95.0,
            confidence=100.0,
        )

        assert result.level == 5

        assert (
            result.category
            == "Immediate Buying Intent"
        )

        assert result.score == 95.0

    # ---------------------------------------------------------
    # SIGNAL NORMALIZATION — HYPHENS
    # ---------------------------------------------------------

    def test_signal_name_normalizes_hyphens(self):
        result = LBITService.classify(
            signal_name="requested-demo",
            score=95.0,
            confidence=100.0,
        )

        assert result.level == 5

    # ---------------------------------------------------------
    # SIGNAL NORMALIZATION — UNDERSCORES
    # ---------------------------------------------------------

    def test_signal_name_normalizes_underscores(self):
        result = LBITService.classify(
            signal_name="Requested_Demo",
            score=95.0,
            confidence=100.0,
        )

        assert result.level == 5

    # ---------------------------------------------------------
    # SIGNAL NORMALIZATION — LEADING/TRAILING SPACES
    # ---------------------------------------------------------

    def test_signal_name_removes_outer_spaces(self):
        result = LBITService.classify(
            signal_name="  requested_demo  ",
            score=95.0,
            confidence=100.0,
        )

        assert result.level == 5

    # ---------------------------------------------------------
    # CONFIDENCE LOWER BOUNDARY
    # ---------------------------------------------------------

    def test_confidence_clamped_to_zero(self):
        result = LBITService.classify(
            signal_name="requested_demo",
            score=95.0,
            confidence=-25.0,
        )

        assert result.confidence == 0.0

    # ---------------------------------------------------------
    # CONFIDENCE UPPER BOUNDARY
    # ---------------------------------------------------------

    def test_confidence_clamped_to_100(self):
        result = LBITService.classify(
            signal_name="requested_demo",
            score=95.0,
            confidence=150.0,
        )

        assert result.confidence == 100.0

    # ---------------------------------------------------------
    # UNKNOWN SIGNAL
    # ---------------------------------------------------------

    def test_unknown_signal_is_not_classified(self):
        with pytest.raises(ValueError):
            LBITService.classify(
                signal_name="unknown_signal",
                score=95.0,
                confidence=100.0,
            )

    # ---------------------------------------------------------
    # UNESTABLISHED SIGNAL
    # ---------------------------------------------------------

    def test_unestablished_signal_is_not_classified(self):
        with pytest.raises(ValueError):
            LBITService.classify(
                signal_name="contract_download",
                score=95.0,
                confidence=100.0,
            )

    # ---------------------------------------------------------
    # EMPTY SIGNAL
    # ---------------------------------------------------------

    def test_empty_signal_name_is_rejected(self):
        with pytest.raises(ValueError):
            LBITService.classify(
                signal_name="",
                score=95.0,
                confidence=100.0,
            )

    # ---------------------------------------------------------
    # NONE SIGNAL
    # ---------------------------------------------------------

    def test_none_signal_name_is_rejected(self):
        with pytest.raises(ValueError):
            LBITService.classify(
                signal_name=None,
                score=95.0,
                confidence=100.0,
            )

    # ---------------------------------------------------------
    # INVALID SCORE
    # ---------------------------------------------------------

    def test_invalid_score_is_rejected(self):
        with pytest.raises(ValueError):
            LBITService.classify(
                signal_name="requested_demo",
                score="not-a-number",
                confidence=100.0,
            )

    # ---------------------------------------------------------
    # NEGATIVE SCORE
    # ---------------------------------------------------------

    def test_negative_score_is_not_level_5(self):
        with pytest.raises(ValueError):
            LBITService.classify(
                signal_name="requested_demo",
                score=-10.0,
                confidence=100.0,
            )

    # ---------------------------------------------------------
    # INVALID CONFIDENCE FALLBACK
    # ---------------------------------------------------------

    def test_invalid_confidence_defaults_to_100(self):
        result = LBITService.classify(
            signal_name="requested_demo",
            score=95.0,
            confidence="invalid",
        )

        assert result.confidence == 100.0