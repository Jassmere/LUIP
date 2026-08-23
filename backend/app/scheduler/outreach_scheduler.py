from app.config import settings

# ---------------------------------------------------------
# Model registration
# ---------------------------------------------------------
#
# The FastAPI application imports app.database during
# normal startup, which registers the complete SQLAlchemy
# model set.
#
# The outreach scheduler can also be executed directly,
# however. In that case we must explicitly load the complete
# model registry before SQLAlchemy initializes relationships.
# ---------------------------------------------------------

from app.models.user import User
from app.models.organization import Organization
from app.models.contract import Contract
from app.models.document import Document
from app.models.clause import Clause

from app.models.company import Company
from app.models.company_score import CompanyScore
from app.models.decision_maker import DecisionMaker
from app.models.buying_activity import BuyingActivity
from app.models.buying_intent_signal import BuyingIntentSignal
from app.models.next_best_action import NextBestAction
from app.models.email_queue import EmailQueue
from app.models.outreach_campaign import OutreachCampaign

from app.db.session import SessionLocal
from app.services.email_service import EmailService


def run_outreach():
    """
    Execute the LUIP outreach queue.

    The scheduler processes prepared EmailQueue records.

    Safety:

        EMAIL_DRY_RUN=True

    prevents actual email transmission.

    Live execution:

        EMAIL_DRY_RUN=False

    enables SMTP transmission, provided valid SMTP
    configuration is available.

    The complete SQLAlchemy model registry is loaded before
    the database session is created so that all relationship()
    targets can be resolved during standalone scheduler
    execution.
    """

    print("")
    print("======================================")
    print("LUIP Outreach Execution Engine")
    print("======================================")
    print("")

    print(
        f"Email dry-run mode: "
        f"{EmailService.is_dry_run()}"
    )

    print(
        f"SMTP configured: "
        f"{EmailService.is_configured()}"
    )

    print(
        f"Email batch size: "
        f"{getattr(settings, 'EMAIL_BATCH_SIZE', 10)}"
    )

    db = SessionLocal()

    try:

        result = (
            EmailService.process_pending_queue(
                db=db,
                limit=getattr(
                    settings,
                    "EMAIL_BATCH_SIZE",
                    10,
                ),
            )
        )

        print("")
        print("Outreach execution result:")

        print(
            f"Processed: "
            f"{result.get('processed', 0)}"
        )

        print(
            f"Sent: "
            f"{result.get('sent', 0)}"
        )

        print(
            f"Failed: "
            f"{result.get('failed', 0)}"
        )

        print(
            f"Dry-run: "
            f"{result.get('dry_run_count', 0)}"
        )

        print("")

        return result

    except Exception as exc:

        print("")
        print(
            "Outreach execution failed:"
        )

        print(str(exc))

        print("")

        return {
            "success": False,
            "processed": 0,
            "sent": 0,
            "failed": 0,
            "dry_run_count": 0,
            "error": str(exc),
        }

    finally:

        db.close()

        print(
            "======================================"
        )

        print(
            "Outreach execution completed."
        )

        print(
            "======================================"
        )

        print("")