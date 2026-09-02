from datetime import datetime, UTC

from sqlalchemy.orm import Session

from app.models.next_best_action import NextBestAction


class NextBestActionService:
    """
    LUIP Next Best Action Engine.

    Converts a company's buying-intent score and optional
    LBIT classification context into an actionable sales
    recommendation.

    Version: 1.3.0
    """

    VERSION = "1.3.0"

    # =====================================================
    # SCORE NORMALISATION
    # =====================================================

    @staticmethod
    def _normalise_score(score: float) -> float:
        """
        Safely normalise a buying-intent score.

        Scores operate on a 0-100 scale.

        Invalid values become 0.
        Negative values become 0.
        Values above 100 are capped at 100.
        """

        try:
            normalised_score = float(score or 0)
        except (TypeError, ValueError):
            normalised_score = 0.0

        if normalised_score < 0:
            return 0.0

        if normalised_score > 100:
            return 100.0

        return normalised_score

    # =====================================================
    # LBIT CONTEXT NORMALISATION
    # =====================================================

    @staticmethod
    def _normalise_lbit_context(
        lbit_level: int | None = None,
        lbit_category: str | None = None,
        lbit_score: float | None = None,
        lbit_confidence: float | None = None,
        signal_name: str | None = None,
    ):
        """
        Normalise optional LBIT context.

        This method deliberately accepts optional values so
        existing LUIP callers remain backward compatible.
        """

        normalised_level = None

        if lbit_level is not None:
            try:
                normalised_level = int(lbit_level)
            except (TypeError, ValueError):
                normalised_level = None

        normalised_category = (
            lbit_category.strip()
            if isinstance(lbit_category, str)
            and lbit_category.strip()
            else None
        )

        normalised_lbit_score = None

        if lbit_score is not None:
            try:
                normalised_lbit_score = (
                    NextBestActionService._normalise_score(
                        lbit_score
                    )
                )
            except (TypeError, ValueError):
                normalised_lbit_score = None

        normalised_confidence = None

        if lbit_confidence is not None:
            try:
                normalised_confidence = float(
                    lbit_confidence
                )
            except (TypeError, ValueError):
                normalised_confidence = None

            if normalised_confidence is not None:
                normalised_confidence = min(
                    max(normalised_confidence, 0.0),
                    100.0,
                )

        normalised_signal_name = (
            signal_name.strip()
            if isinstance(signal_name, str)
            and signal_name.strip()
            else None
        )

        return {
            "level": normalised_level,
            "category": normalised_category,
            "score": normalised_lbit_score,
            "confidence": normalised_confidence,
            "signal_name": normalised_signal_name,
        }

    # =====================================================
    # SCORE → ACTION
    # =====================================================

    @staticmethod
    def get_action(score: float):
        """
        Convert buying-intent score into a recommended
        sales action.

        Existing score thresholds are preserved.
        """

        score = NextBestActionService._normalise_score(
            score
        )

        if score >= 95:
            return {
                "priority": "Critical",
                "action": "Call immediately",
                "sla": "Within 1 hour",
                "recommended_within_hours": 1,
                "reason": (
                    "Immediate buying intent detected"
                ),
            }

        if score >= 85:
            return {
                "priority": "High",
                "action": "Book product demonstration",
                "sla": "Within 4 hours",
                "recommended_within_hours": 4,
                "reason": (
                    "High probability opportunity"
                ),
            }

        if score >= 70:
            return {
                "priority": "Medium",
                "action": "Send personalised email",
                "sla": "Within 24 hours",
                "recommended_within_hours": 24,
                "reason": (
                    "Qualified prospect"
                ),
            }

        if score >= 50:
            return {
                "priority": "Low",
                "action": "Add to nurture campaign",
                "sla": "Within 72 hours",
                "recommended_within_hours": 72,
                "reason": (
                    "Monitor engagement"
                ),
            }

        return {
            "priority": "Cold",
            "action": "Continue monitoring",
            "sla": "No immediate action",
            "recommended_within_hours": 168,
            "reason": (
                "Insufficient buying signals"
            ),
        }

    # =====================================================
    # EXPLANATION GENERATION
    # =====================================================

    @staticmethod
    def build_explanation(
        score: float,
        recommendation: dict,
        lbit_level: int | None = None,
        lbit_category: str | None = None,
        lbit_confidence: float | None = None,
        signal_name: str | None = None,
    ) -> str:
        """
        Build a human-readable explanation for the
        recommended action.

        Existing score-based explanations remain unchanged
        when no LBIT context is supplied.
        """

        base_reason = recommendation["reason"]

        if lbit_level is None:
            return base_reason

        explanation_parts = [
            base_reason
        ]

        if signal_name:
            explanation_parts.append(
                f"Signal: {signal_name}."
            )

        explanation_parts.append(
            f"LBIT Level {lbit_level}"
        )

        if lbit_category:
            explanation_parts.append(
                f"({lbit_category})"
            )

        explanation_parts[-1] += "."

        if lbit_confidence is not None:
            explanation_parts.append(
                "LBIT confidence: "
                f"{lbit_confidence:.0f}%."
            )

        return " ".join(explanation_parts)

    # =====================================================
    # AI REASONING GENERATION
    # =====================================================

    @staticmethod
    def build_ai_reasoning(
        score: float,
        recommendation: dict,
        lbit_level: int | None = None,
        lbit_category: str | None = None,
        lbit_score: float | None = None,
        lbit_confidence: float | None = None,
        signal_name: str | None = None,
    ) -> str:
        """
        Build structured reasoning explaining why the
        recommended action was selected.

        This is deterministic reasoning rather than a
        fabricated external AI response.

        It provides a foundation for a future AI reasoning
        provider without making the current engine dependent
        on an external AI service.
        """

        normalised_score = (
            NextBestActionService._normalise_score(score)
        )

        reasoning_parts = [
            (
                f"Company buying-intent score is "
                f"{normalised_score:.1f}/100."
            ),
            (
                f"LUIP recommends '{recommendation['action']}' "
                f"with {recommendation['priority']} priority."
            ),
        ]

        if recommendation.get(
            "recommended_within_hours"
        ) is not None:
            reasoning_parts.append(
                "Recommended response window is "
                f"{recommendation['recommended_within_hours']} "
                "hour(s)."
            )

        if lbit_level is not None:
            reasoning_parts.append(
                f"LBIT classification is Level "
                f"{lbit_level}."
            )

        if lbit_category:
            reasoning_parts.append(
                f"LBIT category is "
                f"'{lbit_category}'."
            )

        if signal_name:
            reasoning_parts.append(
                f"Triggering signal is "
                f"'{signal_name}'."
            )

        if lbit_score is not None:
            reasoning_parts.append(
                f"LBIT score is "
                f"{float(lbit_score):.1f}/100."
            )

        if lbit_confidence is not None:
            reasoning_parts.append(
                f"LBIT confidence is "
                f"{float(lbit_confidence):.1f}%."
            )

        return " ".join(reasoning_parts)

    # =====================================================
    # IN-MEMORY GENERATION
    # =====================================================

    @staticmethod
    def generate(
        company_name: str,
        score: float,
        lbit_level: int | None = None,
        lbit_category: str | None = None,
        lbit_score: float | None = None,
        lbit_confidence: float | None = None,
        signal_name: str | None = None,
        ai_reasoning: str | None = None,
    ):
        """
        Generate an in-memory Next Best Action
        recommendation.

        LBIT context is optional for backward compatibility.
        """

        normalised_score = (
            NextBestActionService._normalise_score(
                score
            )
        )

        recommendation = (
            NextBestActionService.get_action(
                normalised_score
            )
        )

        lbit_context = (
            NextBestActionService._normalise_lbit_context(
                lbit_level=lbit_level,
                lbit_category=lbit_category,
                lbit_score=lbit_score,
                lbit_confidence=lbit_confidence,
                signal_name=signal_name,
            )
        )

        explanation = (
            NextBestActionService.build_explanation(
                score=normalised_score,
                recommendation=recommendation,
                lbit_level=lbit_context["level"],
                lbit_category=lbit_context["category"],
                lbit_confidence=lbit_context[
                    "confidence"
                ],
                signal_name=lbit_context[
                    "signal_name"
                ],
            )
        )

        reasoning = ai_reasoning

        if reasoning is None and (
            lbit_context["level"] is not None
            or lbit_context["signal_name"] is not None
        ):
            reasoning = (
                NextBestActionService.build_ai_reasoning(
                    score=normalised_score,
                    recommendation=recommendation,
                    lbit_level=lbit_context["level"],
                    lbit_category=lbit_context[
                        "category"
                    ],
                    lbit_score=lbit_context["score"],
                    lbit_confidence=lbit_context[
                        "confidence"
                    ],
                    signal_name=lbit_context[
                        "signal_name"
                    ],
                )
            )

        return {
            "company": company_name,
            "score": normalised_score,
            "generated_at": datetime.now(UTC),
            "explanation": explanation,
            "ai_reasoning": reasoning,
            **recommendation,
        }

    # =====================================================
    # DATABASE ACTION CREATION
    # =====================================================

    @staticmethod
    def create_action(
        db: Session,
        company_id: int,
        score: float,
        ai_reasoning: str | None = None,
        lbit_level: int | None = None,
        lbit_category: str | None = None,
        lbit_score: float | None = None,
        lbit_confidence: float | None = None,
        signal_name: str | None = None,
    ):
        """
        Create or refresh the pending Next Best Action
        for a company.

        Existing completed actions are preserved.

        All LBIT parameters are optional so existing LUIP
        integrations remain backward compatible.
        """

        normalised_score = (
            NextBestActionService._normalise_score(
                score
            )
        )

        recommendation = (
            NextBestActionService.get_action(
                normalised_score
            )
        )

        lbit_context = (
            NextBestActionService._normalise_lbit_context(
                lbit_level=lbit_level,
                lbit_category=lbit_category,
                lbit_score=lbit_score,
                lbit_confidence=lbit_confidence,
                signal_name=signal_name,
            )
        )

        explanation = (
            NextBestActionService.build_explanation(
                score=normalised_score,
                recommendation=recommendation,
                lbit_level=lbit_context["level"],
                lbit_category=lbit_context["category"],
                lbit_confidence=lbit_context[
                    "confidence"
                ],
                signal_name=lbit_context[
                    "signal_name"
                ],
            )
        )

        reasoning = ai_reasoning

        if reasoning is None and (
            lbit_context["level"] is not None
            or lbit_context["signal_name"] is not None
        ):
            reasoning = (
                NextBestActionService.build_ai_reasoning(
                    score=normalised_score,
                    recommendation=recommendation,
                    lbit_level=lbit_context["level"],
                    lbit_category=lbit_context[
                        "category"
                    ],
                    lbit_score=lbit_context["score"],
                    lbit_confidence=lbit_context[
                        "confidence"
                    ],
                    signal_name=lbit_context[
                        "signal_name"
                    ],
                )
            )

        existing = (
            db.query(NextBestAction)
            .filter(
                NextBestAction.company_id == company_id,
                NextBestAction.status == "Pending",
            )
            .order_by(
                NextBestAction.created_at.desc()
            )
            .first()
        )

        # -------------------------------------------------
        # UPDATE EXISTING PENDING ACTION
        # -------------------------------------------------

        if existing:

            existing.action_type = (
                recommendation["action"]
            )

            existing.priority = (
                recommendation["priority"]
            )

            existing.recommended_within_hours = (
                recommendation[
                    "recommended_within_hours"
                ]
            )

            existing.explanation = explanation

            existing.ai_reasoning = reasoning

            db.commit()
            db.refresh(existing)

            return existing

        # -------------------------------------------------
        # CREATE NEW ACTION
        # -------------------------------------------------

        action = NextBestAction(
            company_id=company_id,
            action_type=recommendation["action"],
            priority=recommendation["priority"],
            recommended_within_hours=(
                recommendation[
                    "recommended_within_hours"
                ]
            ),
            explanation=explanation,
            ai_reasoning=reasoning,
            status="Pending",
            created_at=datetime.now(UTC),
        )

        db.add(action)

        db.commit()

        db.refresh(action)

        return action