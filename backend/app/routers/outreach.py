from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company
from app.models.decision_maker import DecisionMaker
from app.models.outreach_campaign import OutreachCampaign
from app.models.email_queue import EmailQueue
from app.services.outreach_service import OutreachService


router = APIRouter(
    prefix="/outreach",
    tags=["Outreach Operations"],
)


# =========================================================
# STATUS DEFINITIONS
# =========================================================

CAMPAIGN_STATUSES = {
    "Draft",
    "Scheduled",
    "Sending",
    "Sent",
    "Cancelled",
}

QUEUE_STATUSES = {
    "Pending",
    "Processing",
    "Sent",
    "Failed",
    "Cancelled",
}


# =========================================================
# HELPERS
# =========================================================

def campaign_to_dict(
    campaign: OutreachCampaign,
):
    return {
        "id": campaign.id,
        "company_id": campaign.company_id,
        "decision_maker_id": campaign.decision_maker_id,
        "campaign_name": campaign.campaign_name,
        "campaign_type": campaign.campaign_type,
        "subject": campaign.subject,
        "message": campaign.message,
        "status": campaign.status,
        "scheduled_for": campaign.scheduled_for,
        "sent_at": campaign.sent_at,
        "opened": campaign.opened,
        "clicked": campaign.clicked,
        "replied": campaign.replied,
        "meeting_booked": campaign.meeting_booked,
        "created_at": campaign.created_at,
        "updated_at": campaign.updated_at,
    }


def queue_to_dict(
    queue: EmailQueue,
):
    return {
        "id": queue.id,
        "company_id": queue.company_id,
        "decision_maker_id": queue.decision_maker_id,
        "campaign_id": queue.campaign_id,
        "recipient_email": queue.recipient_email,
        "recipient_name": queue.recipient_name,
        "subject": queue.subject,
        "priority": queue.priority,
        "status": queue.status,
        "retry_count": queue.retry_count,
        "max_retries": queue.max_retries,
        "scheduled_for": queue.scheduled_for,
        "sent_at": queue.sent_at,
        "error_message": queue.error_message,
        "opened": queue.opened,
        "clicked": queue.clicked,
        "replied": queue.replied,
        "bounced": queue.bounced,
        "created_at": queue.created_at,
        "updated_at": queue.updated_at,
    }


# =========================================================
# PREPARE OUTREACH
# =========================================================

@router.post(
    "/prepare",
)
def prepare_outreach(
    company_id: int,
    decision_maker_id: int | None = None,
    campaign_name: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Prepare outreach for a company.

    This endpoint creates the OutreachCampaign and
    EmailQueue records through OutreachService.

    No email is sent.
    """

    result = OutreachService.create_outreach(
        db=db,
        company_id=company_id,
        decision_maker_id=decision_maker_id,
        campaign_name=campaign_name,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result,
        )

    return result


# =========================================================
# LIST CAMPAIGNS
# =========================================================

@router.get(
    "/campaigns",
)
def list_campaigns(
    company_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """
    List outreach campaigns.

    Optional filters:
        company_id
        status
    """

    query = db.query(
        OutreachCampaign
    )

    if company_id is not None:
        query = query.filter(
            OutreachCampaign.company_id
            == company_id
        )

    if status is not None:

        if status not in CAMPAIGN_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid campaign status: {status}. "
                    f"Allowed statuses: "
                    f"{sorted(CAMPAIGN_STATUSES)}"
                ),
            )

        query = query.filter(
            OutreachCampaign.status
            == status
        )

    campaigns = (
        query
        .order_by(
            OutreachCampaign.created_at.desc()
        )
        .all()
    )

    return {
        "success": True,
        "count": len(campaigns),
        "campaigns": [
            campaign_to_dict(campaign)
            for campaign in campaigns
        ],
    }


# =========================================================
# GET CAMPAIGN
# =========================================================

@router.get(
    "/campaign/{campaign_id}",
)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    """
    Return a single campaign together with
    its associated email queue record.
    """

    campaign = (
        db.query(OutreachCampaign)
        .filter(
            OutreachCampaign.id
            == campaign_id
        )
        .first()
    )

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Outreach campaign "
                f"{campaign_id} not found."
            ),
        )

    queue = (
        db.query(EmailQueue)
        .filter(
            EmailQueue.campaign_id
            == campaign.id
        )
        .order_by(
            EmailQueue.created_at.desc()
        )
        .first()
    )

    return {
        "success": True,
        "campaign": campaign_to_dict(
            campaign
        ),
        "email_queue": (
            queue_to_dict(queue)
            if queue is not None
            else None
        ),
    }


# =========================================================
# LIST EMAIL QUEUE
# =========================================================

@router.get(
    "/queue",
)
def list_queue(
    company_id: int | None = None,
    campaign_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """
    List email queue entries.

    Optional filters:
        company_id
        campaign_id
        status
    """

    query = db.query(
        EmailQueue
    )

    if company_id is not None:
        query = query.filter(
            EmailQueue.company_id
            == company_id
        )

    if campaign_id is not None:
        query = query.filter(
            EmailQueue.campaign_id
            == campaign_id
        )

    if status is not None:

        if status not in QUEUE_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid queue status: {status}. "
                    f"Allowed statuses: "
                    f"{sorted(QUEUE_STATUSES)}"
                ),
            )

        query = query.filter(
            EmailQueue.status
            == status
        )

    queue_entries = (
        query
        .order_by(
            EmailQueue.created_at.desc()
        )
        .all()
    )

    return {
        "success": True,
        "count": len(queue_entries),
        "queue": [
            queue_to_dict(entry)
            for entry in queue_entries
        ],
    }


# =========================================================
# UPDATE CAMPAIGN STATUS
# =========================================================

@router.patch(
    "/campaign/{campaign_id}/status",
)
def update_campaign_status(
    campaign_id: int,
    status: str,
    db: Session = Depends(get_db),
):
    """
    Update operational campaign status.

    This endpoint does not send an email.
    """

    if status not in CAMPAIGN_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid campaign status: {status}. "
                f"Allowed statuses: "
                f"{sorted(CAMPAIGN_STATUSES)}"
            ),
        )

    campaign = (
        db.query(OutreachCampaign)
        .filter(
            OutreachCampaign.id
            == campaign_id
        )
        .first()
    )

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Outreach campaign "
                f"{campaign_id} not found."
            ),
        )

    now = datetime.now(UTC)

    campaign.status = status
    campaign.updated_at = now

    if status == "Sent":
        campaign.sent_at = now

    if status == "Scheduled":
        if campaign.scheduled_for is None:
            campaign.scheduled_for = now

    db.commit()
    db.refresh(campaign)

    return {
        "success": True,
        "message": (
            "Campaign status updated."
        ),
        "campaign": campaign_to_dict(
            campaign
        ),
    }


# =========================================================
# UPDATE QUEUE STATUS
# =========================================================

@router.patch(
    "/queue/{queue_id}/status",
)
def update_queue_status(
    queue_id: int,
    status: str,
    error_message: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Update email queue operational status.

    This endpoint controls queue state only.
    It does not transmit email.
    """

    if status not in QUEUE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid queue status: {status}. "
                f"Allowed statuses: "
                f"{sorted(QUEUE_STATUSES)}"
            ),
        )

    queue = (
        db.query(EmailQueue)
        .filter(
            EmailQueue.id
            == queue_id
        )
        .first()
    )

    if queue is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Email queue entry "
                f"{queue_id} not found."
            ),
        )

    now = datetime.now(UTC)

    queue.status = status
    queue.updated_at = now

    if status == "Sent":
        queue.sent_at = now

    if status == "Failed":

        queue.error_message = (
            error_message
            or "Email delivery failed."
        )

        if (
            queue.retry_count
            is None
        ):
            queue.retry_count = 0

        queue.retry_count += 1

    elif error_message is not None:
        queue.error_message = (
            error_message
        )

    db.commit()
    db.refresh(queue)

    return {
        "success": True,
        "message": (
            "Email queue status updated."
        ),
        "queue": queue_to_dict(queue),
    }


# =========================================================
# RECORD CAMPAIGN ENGAGEMENT
# =========================================================

@router.patch(
    "/campaign/{campaign_id}/engagement",
)
def update_campaign_engagement(
    campaign_id: int,
    opened: bool | None = None,
    clicked: bool | None = None,
    replied: bool | None = None,
    meeting_booked: bool | None = None,
    db: Session = Depends(get_db),
):
    """
    Record engagement activity for a campaign.

    This endpoint records engagement only.
    """

    campaign = (
        db.query(OutreachCampaign)
        .filter(
            OutreachCampaign.id
            == campaign_id
        )
        .first()
    )

    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Outreach campaign "
                f"{campaign_id} not found."
            ),
        )

    if opened is not None:
        campaign.opened = opened

    if clicked is not None:
        campaign.clicked = clicked

    if replied is not None:
        campaign.replied = replied

    if meeting_booked is not None:
        campaign.meeting_booked = (
            meeting_booked
        )

    campaign.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(campaign)

    return {
        "success": True,
        "message": (
            "Campaign engagement updated."
        ),
        "campaign": campaign_to_dict(
            campaign
        ),
    }


# =========================================================
# RECORD QUEUE ENGAGEMENT
# =========================================================

@router.patch(
    "/queue/{queue_id}/engagement",
)
def update_queue_engagement(
    queue_id: int,
    opened: bool | None = None,
    clicked: bool | None = None,
    replied: bool | None = None,
    bounced: bool | None = None,
    db: Session = Depends(get_db),
):
    """
    Record email queue engagement.

    This endpoint records engagement only.
    """

    queue = (
        db.query(EmailQueue)
        .filter(
            EmailQueue.id
            == queue_id
        )
        .first()
    )

    if queue is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Email queue entry "
                f"{queue_id} not found."
            ),
        )

    if opened is not None:
        queue.opened = opened

    if clicked is not None:
        queue.clicked = clicked

    if replied is not None:
        queue.replied = replied

    if bounced is not None:
        queue.bounced = bounced

    queue.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(queue)

    return {
        "success": True,
        "message": (
            "Email queue engagement updated."
        ),
        "queue": queue_to_dict(queue),
    }