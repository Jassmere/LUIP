from datetime import datetime

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.buying_intent_signal import BuyingIntentSignal
from app.models.buying_activity import BuyingActivity

from app.services.lbit_service import LBITService


class BuyingSignalService:
    """
    LUIP Buying Signal Ingestion Service.

    Converts discovered buying-intent signals into:

    1. BuyingIntentSignal records
    2. BuyingActivity records
    3. LBIT classification where a verified taxonomy
       definition exists

    BuyingActivity records are consumed by the
    LUIP Buying Intelligence scoring pipeline.

    Version: 1.2.0
    """

    VERSION = "1.2.0"

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

        LBIT classification is attempted after the basic
        LUIP signal values have been normalized.

        Signals that do not yet have an established LBIT
        taxonomy definition remain valid LUIP signals but
        are stored without an LBIT classification.
        """

        # -------------------------------------------------
        # Validate company
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
        # Validate required fields
        # -------------------------------------------------

        if not signal_name or not signal_name.strip():
            return {
                "success": False,
                "error": "signal_name is required",
            }

        if (
            not signal_category
            or not signal_category.strip()
        ):
            return {
                "success": False,
                "error": "signal_category is required",
            }

        # -------------------------------------------------
        # Normalize text values
        # -------------------------------------------------

        signal_name = signal_name.strip()

        signal_category = (
            signal_category.strip()
        )

        source = (
            source.strip()
            if source
            else None
        )

        source_url = (
            source_url.strip()
            if source_url
            else None
        )

        evidence = (
            evidence.strip()
            if evidence
            else None
        )

        # -------------------------------------------------
        # Normalize score
        # -------------------------------------------------

        try:
            score = float(score)

        except (TypeError, ValueError):
            score = 0.0

        # -------------------------------------------------
        # Normalize confidence
        # -------------------------------------------------

        try:
            confidence = float(confidence)

        except (TypeError, ValueError):
            confidence = 100.0

        # -------------------------------------------------
        # Keep values within sensible ranges
        # -------------------------------------------------

        if score < 0:
            score = 0.0

        if confidence < 0:
            confidence = 0.0

        if confidence > 100:
            confidence = 100.0

        # -------------------------------------------------
        # LBIT CLASSIFICATION
        # -------------------------------------------------

        lbit_classification = None

        try:
            lbit_classification = (
                LBITService.classify(
                    signal_name=signal_name,
                    score=score,
                    confidence=confidence,
                )
            )

        except ValueError:
            # -------------------------------------------------
            # IMPORTANT:
            #
            # An unclassified LBIT signal is NOT rejected.
            #
            # LUIP can continue storing and scoring the
            # buying signal while LBIT remains unclassified.
            # -------------------------------------------------

            lbit_classification = None

        # -------------------------------------------------
        # Create Buying Intent Signal
        # -------------------------------------------------

        detected_at = datetime.utcnow()

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
        # Add LBIT classification where available
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
        # Flush so SQLAlchemy assigns the signal ID
        # -------------------------------------------------

        db.flush()

        # -------------------------------------------------
        # Create Buying Activity
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

            created_at=datetime.utcnow(),
        )

        db.add(activity)

        # -------------------------------------------------
        # Commit signal + activity together
        # -------------------------------------------------

        try:

            db.commit()

        except Exception as exc:

            db.rollback()

            return {
                "success": False,
                "error": (
                    "Unable to save buying signal."
                ),
                "detail": str(exc),
            }

        # -------------------------------------------------
        # Refresh database records
        # -------------------------------------------------

        db.refresh(signal)

        db.refresh(activity)

        # -------------------------------------------------
        # Build LBIT response
        # -------------------------------------------------

        if lbit_classification is not None:

            lbit_result = {
                "classified": True,
                "level": (
                    lbit_classification.level
                ),
                "category": (
                    lbit_classification.category
                ),
                "score": (
                    lbit_classification.score
                ),
                "confidence": (
                    lbit_classification.confidence
                ),
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
        # Return structured result
        # -------------------------------------------------

        return {
            "success": True,

            "version": (
                BuyingSignalService.VERSION
            ),

            "company": {
                "id": company.id,
                "name": company.name,
            },

            "signal": {
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

                "detected_at": (
                    signal.detected_at
                ),
            },

            "lbit": lbit_result,

            "buying_activity": {
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

                "confidence": (
                    activity.confidence
                ),

                "processed": (
                    activity.processed
                ),

                "discovered_at": (
                    activity.discovered_at
                ),

                "created_at": (
                    activity.created_at
                ),
            },
        }

    # -----------------------------------------------------
    # BACKWARD-COMPATIBILITY METHOD
    # -----------------------------------------------------

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

        Existing LUIP code that calls record_signal()
        will continue to work.
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

    # -----------------------------------------------------
    # GET COMPANY SIGNALS
    # -----------------------------------------------------

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
                BuyingIntentSignal.company_id
                == company_id
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

                    "signal_name": (
                        signal.signal_name
                    ),

                    "signal_category": (
                        signal.signal_category
                    ),

                    "source": signal.source,

                    "source_url": (
                        signal.source_url
                    ),

                    "evidence": signal.evidence,

                    "score": signal.score,

                    "confidence": (
                        signal.confidence
                    ),

                    "lbit": {
                        "classified": (
                            signal.lbit_level
                            is not None
                        ),

                        "level": (
                            signal.lbit_level
                        ),

                        "category": (
                            signal.lbit_category
                        ),

                        "score": (
                            signal.lbit_score
                        ),

                        "confidence": (
                            signal.lbit_confidence
                        ),
                    },

                    "detected_at": (
                        signal.detected_at
                    ),
                }

                for signal in signals
            ],
        }

    # -----------------------------------------------------
    # GET COMPANY ACTIVITIES
    # -----------------------------------------------------

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
                BuyingActivity.company_id
                == company_id
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

                    "confidence": (
                        activity.confidence
                    ),

                    "processed": (
                        activity.processed
                    ),

                    "ai_summary": (
                        activity.ai_summary
                    ),

                    "ai_recommendation": (
                        activity.ai_recommendation
                    ),

                    "discovered_at": (
                        activity.discovered_at
                    ),

                    "created_at": (
                        activity.created_at
                    ),
                }

                for activity in activities
            ],
        }