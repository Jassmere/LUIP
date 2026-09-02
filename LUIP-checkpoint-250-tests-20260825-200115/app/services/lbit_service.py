from dataclasses import dataclass


@dataclass(frozen=True)
class LBITClassification:
    """
    Legal Buying Intent Taxonomy classification.

    This initial implementation contains only the
    LBIT rules currently established for LUIP Level 5.

    Unknown or not-yet-established signals are deliberately
    not classified.
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

    # ---------------------------------------------------------
    # LEVEL 5 — IMMEDIATE BUYING INTENT
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # SIGNAL NORMALIZATION
    # ---------------------------------------------------------

    @staticmethod
    def normalize_signal_name(signal_name: str) -> str:
        """
        Convert a raw signal name into a canonical format.

        Examples:

            "Requested Demo"
                -> "requested_demo"

            "requested-demo"
                -> "requested_demo"

            "Requested_Demo"
                -> "requested_demo"

            "  requested demo  "
                -> "requested_demo"

        Raises:
            ValueError: if signal_name is empty or invalid.
        """

        if signal_name is None:
            raise ValueError("signal_name is required")

        if not isinstance(signal_name, str):
            raise ValueError("signal_name must be a string")

        normalized_name = signal_name.strip().lower()

        if not normalized_name:
            raise ValueError("signal_name is required")

        # Treat spaces and hyphens consistently.
        normalized_name = normalized_name.replace("-", "_")
        normalized_name = normalized_name.replace(" ", "_")

        # Collapse repeated underscores.
        while "__" in normalized_name:
            normalized_name = normalized_name.replace(
                "__",
                "_",
            )

        return normalized_name

    # ---------------------------------------------------------
    # SCORE NORMALIZATION
    # ---------------------------------------------------------

    @staticmethod
    def normalize_score(score: float) -> float:
        """
        Convert score to float and prevent negative scores.

        LBIT Level 5 classification itself requires a score
        between 90 and 100.
        """

        try:
            normalized_score = float(score)
        except (TypeError, ValueError):
            raise ValueError(
                "score must be a valid numeric value"
            )

        if normalized_score < 0:
            normalized_score = 0.0

        return normalized_score

    # ---------------------------------------------------------
    # CONFIDENCE NORMALIZATION
    # ---------------------------------------------------------

    @staticmethod
    def normalize_confidence(confidence: float) -> float:
        """
        Convert confidence to float and clamp it between
        0 and 100.
        """

        try:
            normalized_confidence = float(confidence)
        except (TypeError, ValueError):
            normalized_confidence = 100.0

        normalized_confidence = min(
            max(normalized_confidence, 0.0),
            100.0,
        )

        return normalized_confidence

    # ---------------------------------------------------------
    # CLASSIFICATION
    # ---------------------------------------------------------

    @staticmethod
    def classify(
        signal_name: str,
        score: float,
        confidence: float = 100.0,
    ) -> LBITClassification:
        """
        Classify a buying signal using the established
        LBIT Level 5 rules.

        Signals not yet defined in the verified LBIT
        specification are deliberately not classified.

        Args:
            signal_name:
                Raw buying signal name.

            score:
                LUIP buying-intent score.

            confidence:
                Confidence percentage from 0 to 100.

        Returns:
            LBITClassification

        Raises:
            ValueError:
                If the signal cannot currently be classified.
        """

        # -----------------------------------------------------
        # Normalize inputs
        # -----------------------------------------------------

        normalized_name = (
            LBITService.normalize_signal_name(signal_name)
        )

        normalized_score = (
            LBITService.normalize_score(score)
        )

        normalized_confidence = (
            LBITService.normalize_confidence(confidence)
        )

        # -----------------------------------------------------
        # Level 5 classification
        # -----------------------------------------------------

        if (
            normalized_name
            in LBITService.LEVEL_5_SIGNALS
            and LBITService.LEVEL_5_MIN_SCORE
            <= normalized_score
            <= LBITService.LEVEL_5_MAX_SCORE
        ):
            return LBITClassification(
                level=5,
                category=LBITService.LEVEL_5_CATEGORY,
                score=normalized_score,
                confidence=normalized_confidence,
                signal_name=signal_name.strip(),
            )

        # -----------------------------------------------------
        # Signal not yet established in LBIT
        # -----------------------------------------------------

        raise ValueError(
            f"Signal '{signal_name}' cannot currently be "
            "classified because its LBIT taxonomy definition "
            "has not yet been established."
        )