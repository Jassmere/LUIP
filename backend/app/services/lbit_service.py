from dataclasses import dataclass


@dataclass(frozen=True)
class LBITClassification:
    """
    Legal Buying Intent Taxonomy classification.

    This initial implementation contains only the
    LBIT rules currently established for LUIP Level 5.
    """

    level: int
    category: str
    score: float
    confidence: float
    signal_name: str


class LBITService:
    """
    LUIP Legal Buying Intent Taxonomy Service.

    LBIT is the classification layer between raw buying
    signals and the LUIP buying-intelligence scoring engine.

    Version: 1.2.0
    """

    VERSION = "1.2.0"

    LEVEL_5_MIN_SCORE = 90.0
    LEVEL_5_MAX_SCORE = 100.0

    LEVEL_5_CATEGORY = "Immediate Buying Intent"

    LEVEL_5_SIGNALS = {
        "requested_demo",
        "pricing_page_repeat_visit",
        "feature_request_response",
        "clm_rfp",
        "clm_rfq",
        "proposal_request",
    }

    @staticmethod
    def classify(
        signal_name: str,
        score: float,
        confidence: float = 100.0,
    ) -> LBITClassification:
        """
        Classify a buying signal using the established
        Level 5 LBIT rules.

        Signals not yet defined in the verified LBIT
        specification are deliberately not classified.
        """

        normalized_name = (
            signal_name.strip().lower().replace(" ", "_")
        )

        score = float(score)
        confidence = float(confidence)

        confidence = min(
            max(confidence, 0.0),
            100.0,
        )

        if (
            normalized_name in LBITService.LEVEL_5_SIGNALS
            and LBITService.LEVEL_5_MIN_SCORE
            <= score
            <= LBITService.LEVEL_5_MAX_SCORE
        ):
            return LBITClassification(
                level=5,
                category=LBITService.LEVEL_5_CATEGORY,
                score=score,
                confidence=confidence,
                signal_name=signal_name,
            )

        raise ValueError(
            f"Signal '{signal_name}' cannot currently be "
            "classified because its LBIT taxonomy definition "
            "has not yet been established."
        )