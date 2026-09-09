from app.config import settings

# ---------------------------------------------------------
# Model registration
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


def run_outreach():
    """
    Execute LUIP outreach preparation only.

    Automatic email transmission is deliberately disabled.

    Pilot flow:

        Intelligence
            ->
        Buying Intent Classification
            ->
        Next Best Action
            ->
        Outreach Generation
            ->
        Email Queue
            ->
        Manual Review / Approval
            ->
        Manual Send

    This scheduler does NOT call:
        EmailService.process_pending_queue()
        EmailService.send_email()
    """

    print("")
    print("======================================")
    print("LUIP Outreach Preparation Scheduler")
    print("======================================")
    print("")

    print("Automatic email transmission: DISABLED")
    print("Manual send required: ENABLED")

    print(
        f"Email batch size: "
        f"{getattr(settings, 'EMAIL_BATCH_SIZE', 10)}"
    )

    db = SessionLocal()

    try:
        pending_count = (
            db.query(EmailQueue)
            .filter(
                EmailQueue.status == "Pending"
            )
            .count()
        )

        draft_campaign_count = (
            db.query(OutreachCampaign)
            .filter(
                OutreachCampaign.status == "Draft"
            )
            .count()
        )

        print("")
        print("Outreach preparation status:")

        print(
            f"Pending email queue entries: "
            f"{pending_count}"
        )

        print(
            f"Draft outreach campaigns: "
            f"{draft_campaign_count}"
        )

        print("")
        print("No email transmission was attempted.")

        result = {
            "success": True,
            "automatic_send": False,
            "manual_send_required": True,
            "processed": 0,
            "sent": 0,
            "failed": 0,
            "dry_run_count": 0,
            "pending_count": pending_count,
            "draft_campaign_count": draft_campaign_count,
        }

        print("")
        print("Outreach preparation result:")

        print(
            f"Pending: "
            f"{pending_count}"
        )

        print(
            f"Draft campaigns: "
            f"{draft_campaign_count}"
        )

        print("Sent automatically: 0")
        print("Manual approval/send required: YES")

        print("")

        return result

    except Exception as exc:

        print("")
        print("Outreach preparation failed:")
        print(str(exc))
        print("")

        return {
            "success": False,
            "automatic_send": False,
            "manual_send_required": True,
            "processed": 0,
            "sent": 0,
            "failed": 0,
            "dry_run_count": 0,
            "pending_count": 0,
            "draft_campaign_count": 0,
            "error": str(exc),
        }

    finally:

        db.close()

        print(
            "======================================"
        )

        print(
            "Outreach preparation completed."
        )

        print(
            "Automatic transmission: DISABLED."
        )

        print(
            "======================================"
        )

        print("")


if __name__ == "__main__":
    run_outreach()