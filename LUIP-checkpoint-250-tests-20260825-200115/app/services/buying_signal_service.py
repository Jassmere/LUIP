from datetime import datetime, UTC

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.buying_intent_signal import BuyingIntentSignal
from app.models.buying_activity import BuyingActivity

from app.services.lbit_service import LBITService
from app.services.buying_intelligence_service import (
    BuyingIntelligenceService,
)
from app.services.next_best_action_service import (
    NextBestActionService,
)


class BuyingSignalService:
    """
    LUIP Buying Signal Ingestion Service.

    Converts discovered buying-intent signals into:

    1. BuyingIntentSignal records
    2. BuyingActivity records
    3. LBIT classification where a verified taxonomy
       definition exists
    4. Company-level buying-intent scoring
    5. Next Best Action recommendations
    6. Explainable AI reasoning

    Version: 1.3.0
    """

    VERSION = "1.3.0"

    # =====================================================
    # EXPLAINABLE REASONING
    # =====================================================

    @staticmethod
    def _build_ai_reasoning(
        company_name: str,
        signal_name: str,
        signal_category: str,
        score: float,
        confidence: float,
        evidence: str | None,
        lbit_classification=None,
        company_score=None,
        next_best_action=None,
    ) -> str:
        """
        Build deterministic explainable reasoning for a
        Next Best Action.

        This is LUIP Explainable Reasoning v1.

        It deliberately does not call an external AI model.
        The output is deterministic and auditable.

        A future AI/LLM layer can replace or enrich this
        reasoning without changing the underlying signal,
        LBIT, scoring, or Next Best Action pipeline.
        """

        reasoning_parts = []

        # -------------------------------------------------
        # COMPANY
        # -------------------------------------------------

        reasoning_parts.append(
            f"Company '{company_name}' generated a buying-intent "
            f"signal of '{signal_name}'."
        )

        # -------------------------------------------------
        # SIGNAL CATEGORY
        # -------------------------------------------------

        reasoning_parts.append(
            f"The signal belongs to the '{signal_category}' "
            f"category and carries a score of "
            f"{float(score):.1f}/100 with "
            f"{float(confidence):.1f}% confidence."
        )

        # -------------------------------------------------
        # EVIDENCE
        # -------------------------------------------------

        if evidence:
            reasoning_parts.append(
                f"Supporting evidence: {evidence}"
            )

        # -------------------------------------------------
        # LBIT
        # -------------------------------------------------

        if lbit_classification is not None:
            reasoning_parts.append(
                f"LBIT classified this signal as Level "
                f"{lbit_classification.level} "
                f"('{lbit_classification.category}') "
                f"with a classification score of "
                f"{float(lbit_classification.score):.1f} "
                f"and confidence of "
                f"{float(lbit_classification.confidence):.1f}%."
            )

        else:
            reasoning_parts.append(
                "The signal does not currently have an "
                "established LBIT taxonomy classification."
            )

        # -------------------------------------------------
        # COMPANY-LEVEL SCORE
        # -------------------------------------------------

        if company_score is not None:
            company_buying_score = (
                company_score.buying_intent_score
            )

            company_confidence = (
                company_score.confidence
            )

            reasoning_parts.append(
                f"The resulting company-level buying-intent "
                f"score is {float(company_buying_score):.1f}/100 "
                f"with {float(company_confidence):.1f}% confidence."
            )

        # -------------------------------------------------
        # NEXT BEST ACTION
        # -------------------------------------------------

        if next_best_action is not None:

            action_type = (
                next_best_action.action_type
            )

            priority = (
                next_best_action.priority
            )

            recommended_hours = (
                next_best_action.recommended_within_hours
            )

            reasoning_parts.append(
                f"Based on the available buying-intent "
                f"evidence, LUIP recommends '{action_type}' "
                f"with '{priority}' priority."
            )

            if recommended_hours == 1:
                reasoning_parts.append(
                    "The recommended response window is "
                    "within 1 hour because the opportunity "
                    "indicates immediate buying intent."
                )

            elif recommended_hours < 24:
                reasoning_parts.append(
                    f"The recommended response window is "
                    f"within {recommended_hours} hours because "
                    f"the opportunity requires prompt follow-up."
                )

            elif recommended_hours < 168:
                reasoning_parts.append(
                    f"The recommended response window is "
                    f"within {recommended_hours} hours."
                )

            else:
                reasoning_parts.append(
                    "No immediate sales response is required; "
                    "continued monitoring is recommended."
                )

        # -------------------------------------------------
        # FINAL REASONING
        # -------------------------------------------------

        return " ".join(reasoning_parts)

    # =====================================================
    # CREATE BUYING SIGNAL
    # =====================================================

    @staticmethod
    def create_signal(
        db: Session,
        company_id: int,
        signal_name: str,
        signal_category: str,
        source: str | None = None,
        source_url: str | None = None,
        evidence: str | None = None,
        score: float = 0.0,
        confidence: float = 100.0,
    ):
        """
        Create a buying-intent signal and corresponding
        BuyingActivity record.

        Processing pipeline:

            Signal
                ↓
            LBIT Classification
                ↓
            BuyingIntentSignal
                ↓
            BuyingActivity
                ↓
            Company Buying-Intent Score
                ↓
            Next Best Action
                ↓
            Explainable Reasoning

        Signals without an established LBIT taxonomy
        definition remain valid LUIP signals but are
        stored without an LBIT classification.
        """

        # -------------------------------------------------
        # VALIDATE REQUIRED TEXT FIELDS
        # -------------------------------------------------

        if not signal_name or not signal_name.strip():
            return {
                "success": False,
                "error": "signal_name is required",
            }

        if not signal_category or not signal_category.strip():
            return {
                "success": False,
                "error": "signal_category is required",
            }

        # -------------------------------------------------
        # NORMALIZE TEXT VALUES
        # -------------------------------------------------

        signal_name = signal_name.strip()
        signal_category = signal_category.strip()

        source = (
            source.strip()
            if source and source.strip()
            else None
        )

        source_url = (
            source_url.strip()
            if source_url and source_url.strip()
            else None
        )

        evidence = (
            evidence.strip()
            if evidence and evidence.strip()
            else None
        )

        # -------------------------------------------------
        # NORMALIZE SCORE
        # -------------------------------------------------

        try:
            score = float(score)
        except (TypeError, ValueError):
            score = 0.0

        # -------------------------------------------------
        # NORMALIZE CONFIDENCE
        # -------------------------------------------------

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 100.0

        # -------------------------------------------------
        # CLAMP SCORE
        # -------------------------------------------------

        score = max(
            0.0,
            min(100.0, score),
        )

        # -------------------------------------------------
        # CLAMP CONFIDENCE
        # -------------------------------------------------

        confidence = max(
            0.0,
            min(100.0, confidence),
        )

        # -------------------------------------------------
        # VALIDATE COMPANY
        # -------------------------------------------------

        company = (
            db.query(Company)
            .filter(Company.id == company_id)
            .first()
        )

        if company is None:
            return {
                "success": False,
                "error": f"Company {company_id} not found.",
            }

        # -------------------------------------------------
        # LBIT CLASSIFICATION
        # -------------------------------------------------

        lbit_classification = None

        try:
            lbit_classification = LBITService.classify(
                signal_name=signal_name,
                score=score,
                confidence=confidence,
            )

        except ValueError:
            # An unclassified signal remains a valid LUIP
            # buying signal.
            lbit_classification = None

        # -------------------------------------------------
        # CREATE BUYING INTENT SIGNAL
        # -------------------------------------------------

        detected_at = datetime.now(UTC)

        signal = BuyingIntentSignal(
            company_id=company_id,
            signal_name=signal_name,
            signal_category=signal_category,
            source=source,
            source_url=source_url,
            evidence=evidence,
            score=score,
            confidence=confidence,
            detected_at=detected_at,
        )

        # -------------------------------------------------
        # ADD LBIT CLASSIFICATION
        # -------------------------------------------------

        if lbit_classification is not None:

            signal.lbit_level = (
                lbit_classification.level
            )

            signal.lbit_category = (
                lbit_classification.category
            )

            signal.lbit_score = (
                lbit_classification.score
            )

            signal.lbit_confidence = (
                lbit_classification.confidence
            )

        db.add(signal)

        # -------------------------------------------------
        # FLUSH SIGNAL
        # -------------------------------------------------

        db.flush()

        # -------------------------------------------------
        # CREATE BUYING ACTIVITY
        # -------------------------------------------------

        activity = BuyingActivity(
            company_id=company_id,
            activity_type=signal_category,
            activity_source=source,
            title=signal_name,
            description=evidence,
            url=source_url,
            buying_score=score,
            confidence=confidence,
            processed=False,
            discovered_at=detected_at,
            created_at=datetime.now(UTC),
        )

        db.add(activity)

        # -------------------------------------------------
        # COMMIT SIGNAL + ACTIVITY
        # -------------------------------------------------

        try:

            db.commit()

        except Exception as exc:

            db.rollback()

            return {
                "success": False,
                "error": "Unable to save buying signal.",
                "detail": str(exc),
            }

        # -------------------------------------------------
        # REFRESH DATABASE RECORDS
        # -------------------------------------------------

        db.refresh(signal)
        db.refresh(activity)

        # -------------------------------------------------
        # CALCULATE COMPANY BUYING SCORE
        # -------------------------------------------------

        try:

            company_score = (
                BuyingIntelligenceService.calculate_company_score(
                    db=db,
                    company_id=company_id,
                )
            )

        except Exception as exc:

            return {
                "success": False,
                "error": (
                    "Buying signal saved, but company "
                    "score calculation failed."
                ),
                "detail": str(exc),
                "signal_id": signal.id,
                "activity_id": activity.id,
            }

        # -------------------------------------------------
        # DETERMINE COMPANY SCORE VALUES
        # -------------------------------------------------

        calculated_score = (
            company_score.buying_intent_score
            if company_score is not None
            else score
        )

        calculated_confidence = (
            company_score.confidence
            if company_score is not None
            else confidence
        )

        calculated_priority = (
            company_score.priority
            if company_score is not None
            else "Low"
        )

        # -------------------------------------------------
        # NEXT BEST ACTION
        # -------------------------------------------------

        try:

            next_best_action = (
                NextBestActionService.create_action(
                    db=db,
                    company_id=company_id,
                    score=calculated_score,
                    ai_reasoning=None,
                )
            )

        except Exception as exc:

            return {
                "success": False,
                "error": (
                    "Buying signal and company score saved, "
                    "but Next Best Action generation failed."
                ),
                "detail": str(exc),
                "signal_id": signal.id,
                "activity_id": activity.id,
                "company_score": {
                    "buying_intent_score": calculated_score,
                    "confidence": calculated_confidence,
                    "priority": calculated_priority,
                },
            }

        # -------------------------------------------------
        # BUILD EXPLAINABLE REASONING
        # -------------------------------------------------

        ai_reasoning = (
            BuyingSignalService._build_ai_reasoning(
                company_name=company.name,
                signal_name=signal.signal_name,
                signal_category=signal.signal_category,
                score=score,
                confidence=confidence,
                evidence=evidence,
                lbit_classification=lbit_classification,
                company_score=company_score,
                next_best_action=next_best_action,
            )
        )

        # -------------------------------------------------
        # SAVE EXPLAINABLE REASONING
        # -------------------------------------------------

        try:

            next_best_action.ai_reasoning = (
                ai_reasoning
            )

            db.commit()
            db.refresh(next_best_action)

        except Exception as exc:

            db.rollback()

            return {
                "success": False,
                "error": (
                    "Next Best Action was created, "
                    "but explainable reasoning could not "
                    "be saved."
                ),
                "detail": str(exc),
                "signal_id": signal.id,
                "activity_id": activity.id,
                "next_best_action_id": (
                    next_best_action.id
                ),
            }

        # -------------------------------------------------
        # BUILD LBIT RESULT
        # -------------------------------------------------

        if lbit_classification is not None:

            lbit_result = {
                "classified": True,
                "level": lbit_classification.level,
                "category": lbit_classification.category,
                "score": lbit_classification.score,
                "confidence": lbit_classification.confidence,
            }

        else:

            lbit_result = {
                "classified": False,
                "level": None,
                "category": None,
                "score": None,
                "confidence": None,
            }

        # -------------------------------------------------
        # RETURN STRUCTURED RESULT
        #
        # The response intentionally contains BOTH:
        #
        # 1. Nested modern LUIP structures
        # 2. Flat backward-compatible fields
        #
        # This keeps current routers and downstream
        # LUIP integrations compatible.
        # -------------------------------------------------

        return {
            "success": True,

            "version": BuyingSignalService.VERSION,

            # -------------------------------------------------
            # BACKWARD-COMPATIBLE FLAT COMPANY FIELDS
            # -------------------------------------------------

            "company_id": company.id,
            "company_name": company.name,

            # -------------------------------------------------
            # BACKWARD-COMPATIBLE FLAT SIGNAL FIELDS
            # -------------------------------------------------

            "signal_id": signal.id,
            "signal_name": signal.signal_name,
            "signal_category": signal.signal_category,
            "source": signal.source,
            "source_url": signal.source_url,
            "evidence": signal.evidence,
            "score": signal.score,
            "confidence": signal.confidence,

            # -------------------------------------------------
            # BACKWARD-COMPATIBLE FLAT LBIT FIELDS
            # -------------------------------------------------

            "lbit_level": (
                lbit_classification.level
                if lbit_classification is not None
                else None
            ),

            "lbit_category": (
                lbit_classification.category
                if lbit_classification is not None
                else None
            ),

            "lbit_score": (
                lbit_classification.score
                if lbit_classification is not None
                else None
            ),

            "lbit_confidence": (
                lbit_classification.confidence
                if lbit_classification is not None
                else None
            ),

            # -------------------------------------------------
            # NESTED COMPANY
            # -------------------------------------------------

            "company": {
                "id": company.id,
                "name": company.name,
            },

            # -------------------------------------------------
            # NESTED SIGNAL
            # -------------------------------------------------

            "signal": {
                "id": signal.id,
                "signal_name": signal.signal_name,
                "signal_category": signal.signal_category,
                "source": signal.source,
                "source_url": signal.source_url,
                "evidence": signal.evidence,
                "score": signal.score,
                "confidence": signal.confidence,
                "detected_at": signal.detected_at,
            },

            # -------------------------------------------------
            # NESTED LBIT
            # -------------------------------------------------

            "lbit": lbit_result,

            # -------------------------------------------------
            # COMPANY SCORE
            # -------------------------------------------------

            "company_score": {
                "buying_intent_score": calculated_score,
                "confidence": calculated_confidence,
                "priority": calculated_priority,
                "last_updated": (
                    company_score.last_updated
                    if company_score is not None
                    else None
                ),
            },

            # -------------------------------------------------
            # NEXT BEST ACTION
            # -------------------------------------------------

            "next_best_action": {
                "id": (
                    next_best_action.id
                    if next_best_action is not None
                    else None
                ),
                "action_type": (
                    next_best_action.action_type
                    if next_best_action is not None
                    else None
                ),
                "priority": (
                    next_best_action.priority
                    if next_best_action is not None
                    else None
                ),
                "recommended_within_hours": (
                    next_best_action.recommended_within_hours
                    if next_best_action is not None
                    else None
                ),
                "explanation": (
                    next_best_action.explanation
                    if next_best_action is not None
                    else None
                ),
                "ai_reasoning": (
                    next_best_action.ai_reasoning
                    if next_best_action is not None
                    else None
                ),
                "status": (
                    next_best_action.status
                    if next_best_action is not None
                    else None
                ),
                "created_at": (
                    next_best_action.created_at
                    if next_best_action is not None
                    else None
                ),
            },

            # -------------------------------------------------
            # BUYING ACTIVITY
            # -------------------------------------------------

            "buying_activity": {
                "id": activity.id,
                "activity_type": activity.activity_type,
                "activity_source": activity.activity_source,
                "title": activity.title,
                "description": activity.description,
                "url": activity.url,
                "buying_score": activity.buying_score,
                "confidence": activity.confidence,
                "processed": activity.processed,
                "ai_summary": activity.ai_summary,
                "ai_recommendation": activity.ai_recommendation,
                "discovered_at": activity.discovered_at,
                "created_at": activity.created_at,
            },
        }

    # =====================================================
    # BACKWARD COMPATIBILITY
    # =====================================================

    @staticmethod
    def record_signal(
        db: Session,
        company_id: int,
        signal_name: str,
        signal_category: str,
        source: str | None = None,
        source_url: str | None = None,
        evidence: str | None = None,
        score: float = 0.0,
        confidence: float = 100.0,
    ):
        """
        Backward-compatible alias for create_signal().
        """

        return BuyingSignalService.create_signal(
            db=db,
            company_id=company_id,
            signal_name=signal_name,
            signal_category=signal_category,
            source=source,
            source_url=source_url,
            evidence=evidence,
            score=score,
            confidence=confidence,
        )

    # =====================================================
    # GET COMPANY SIGNALS
    # =====================================================

    @staticmethod
    def get_company_signals(
        db: Session,
        company_id: int,
    ):
        """
        Return all buying-intent signals for a company,
        including LBIT classification where available.
        """

        company = (
            db.query(Company)
            .filter(Company.id == company_id)
            .first()
        )

        if company is None:
            return {
                "success": False,
                "error": "Company not found",
            }

        signals = (
            db.query(BuyingIntentSignal)
            .filter(
                BuyingIntentSignal.company_id == company_id
            )
            .order_by(
                BuyingIntentSignal.detected_at.desc()
            )
            .all()
        )

        return {
            "success": True,
            "company_id": company.id,
            "company": company.name,
            "signals": [
                {
                    "id": signal.id,
                    "signal_name": signal.signal_name,
                    "signal_category": (
                        signal.signal_category
                    ),
                    "source": signal.source,
                    "source_url": signal.source_url,
                    "evidence": signal.evidence,
                    "score": signal.score,
                    "confidence": signal.confidence,
                    "lbit": {
                        "classified": (
                            signal.lbit_level is not None
                        ),
                        "level": signal.lbit_level,
                        "category": signal.lbit_category,
                        "score": signal.lbit_score,
                        "confidence": (
                            signal.lbit_confidence
                        ),
                    },
                    "detected_at": signal.detected_at,
                }
                for signal in signals
            ],
        }

    # =====================================================
    # GET COMPANY ACTIVITIES
    # =====================================================

    @staticmethod
    def get_company_activities(
        db: Session,
        company_id: int,
    ):
        """
        Return all buying activities for a company.
        """

        company = (
            db.query(Company)
            .filter(Company.id == company_id)
            .first()
        )

        if company is None:
            return {
                "success": False,
                "error": "Company not found",
            }

        activities = (
            db.query(BuyingActivity)
            .filter(
                BuyingActivity.company_id == company_id
            )
            .order_by(
                BuyingActivity.discovered_at.desc()
            )
            .all()
        )

        return {
            "success": True,
            "company_id": company.id,
            "company": company.name,
            "activities": [
                {
                    "id": activity.id,
                    "activity_type": (
                        activity.activity_type
                    ),
                    "activity_source": (
                        activity.activity_source
                    ),
                    "title": activity.title,
                    "description": (
                        activity.description
                    ),
                    "url": activity.url,
                    "buying_score": (
                        activity.buying_score
                    ),
                    "confidence": activity.confidence,
                    "processed": activity.processed,
                    "ai_summary": activity.ai_summary,
                    "ai_recommendation": (
                        activity.ai_recommendation
                    ),
                    "discovered_at": (
                        activity.discovered_at
                    ),
                    "created_at": activity.created_at,
                }
                for activity in activities
            ],
        }