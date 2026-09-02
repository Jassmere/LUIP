from datetime import datetime, UTC

from sqlalchemy.orm import Session

from app.config import settings
from app.models.company import Company
from app.models.decision_maker import DecisionMaker
from app.models.next_best_action import NextBestAction
from app.models.outreach_campaign import OutreachCampaign
from app.models.email_queue import EmailQueue


class OutreachService:
    """
    LUIP Outreach Preparation Service.

    Converts an existing Next Best Action and available
    decision-maker information into an outreach campaign
    and email queue entry.

    This service PREPARES outreach.

    It does not send emails.

    Version: 1.0.0
    """

    VERSION = "1.0.0"

    # =====================================================
    # DECISION MAKER
    # =====================================================

    @staticmethod
    def get_decision_maker(
        db: Session,
        company_id: int,
        decision_maker_id: int | None = None,
    ):
        """
        Find a suitable decision maker for a company.

        If decision_maker_id is supplied, that exact
        decision maker is used after validating ownership.

        Otherwise the first decision maker with an email
        address is selected.
        """

        if decision_maker_id is not None:

            decision_maker = (
                db.query(DecisionMaker)
                .filter(
                    DecisionMaker.id
                    == decision_maker_id,
                    DecisionMaker.company_id
                    == company_id,
                )
                .first()
            )

            if decision_maker is None:
                return None

            return decision_maker

        return (
            db.query(DecisionMaker)
            .filter(
                DecisionMaker.company_id
                == company_id,
                DecisionMaker.email.isnot(None),
            )
            .order_by(
                DecisionMaker.id.asc()
            )
            .first()
        )

    # =====================================================
    # NEXT BEST ACTION
    # =====================================================

    @staticmethod
    def get_pending_nba(
        db: Session,
        company_id: int,
    ):
        """
        Return the most recent pending Next Best Action
        for the company.
        """

        return (
            db.query(NextBestAction)
            .filter(
                NextBestAction.company_id
                == company_id,
                NextBestAction.status
                == "Pending",
            )
            .order_by(
                NextBestAction.created_at.desc()
            )
            .first()
        )

    # =====================================================
    # SUBJECT GENERATION
    # =====================================================

    @staticmethod
    def build_subject(
        company: Company,
        decision_maker: DecisionMaker,
        nba: NextBestAction,
    ) -> str:
        """
        Build a deterministic personalised outreach subject.
        """

        if nba.priority == "Critical":
            return (
                f"Following up on {company.name}'s "
                "legal workflow requirements"
            )

        if nba.priority == "High":
            return (
                f"Exploring legal workflow automation "
                f"for {company.name}"
            )

        if nba.priority == "Medium":
            return (
                f"Improving contract workflows at "
                f"{company.name}"
            )

        return (
            f"Legal workflow automation for "
            f"{company.name}"
        )

    # =====================================================
    # MESSAGE GENERATION
    # =====================================================

    @staticmethod
    def build_message(
        company: Company,
        decision_maker: DecisionMaker,
        nba: NextBestAction,
    ) -> str:
        """
        Build a deterministic personalised outreach message.

        This is preparation content only. It does not call
        an external AI provider.
        """

        recipient_name = (
            decision_maker.full_name
            if decision_maker.full_name
            else "there"
        )

        title = (
            decision_maker.title
            if decision_maker.title
            else "your team"
        )

        message = (
            f"Hi {recipient_name},\n\n"
            f"I am reaching out regarding legal workflow "
            f"and contract management at {company.name}.\n\n"
            f"Based on the buying-intent activity identified "
            f"for {company.name}, LUIP currently recommends: "
            f"{nba.action_type}.\n\n"
            f"This recommendation has been assigned "
            f"{nba.priority} priority with a recommended "
            f"response window of "
            f"{nba.recommended_within_hours} hour(s).\n\n"
            f"We believe Lawyered Up can help {title} "
            f"reduce manual contract work, improve legal "
            f"workflow visibility, and accelerate the "
            f"contract lifecycle from draft to signed.\n\n"
            f"If this is relevant to your current priorities, "
            f"I would be happy to arrange a brief discussion.\n\n"
            f"Kind regards,\n"
            f"Lawyered Up"
        )

        return message

    # =====================================================
    # DUPLICATE CHECK
    # =====================================================

    @staticmethod
    def find_existing_pending_campaign(
        db: Session,
        company_id: int,
        decision_maker_id: int,
    ):
        """
        Prevent duplicate pending campaigns for the same
        company and decision maker.
        """

        return (
            db.query(OutreachCampaign)
            .filter(
                OutreachCampaign.company_id
                == company_id,
                OutreachCampaign.decision_maker_id
                == decision_maker_id,
                OutreachCampaign.status
                == "Draft",
            )
            .order_by(
                OutreachCampaign.created_at.desc()
            )
            .first()
        )

    # =====================================================
    # CREATE OUTREACH
    # =====================================================

    @staticmethod
    def create_outreach(
        db: Session,
        company_id: int,
        decision_maker_id: int | None = None,
        campaign_name: str | None = None,
    ):
        """
        Prepare outreach for a company.

        Pipeline:

            Company
                ↓
            Decision Maker
                ↓
            Pending NBA
                ↓
            Outreach Campaign
                ↓
            Email Queue

        No email is sent by this method.
        """

        # -------------------------------------------------
        # VALIDATE COMPANY
        # -------------------------------------------------

        company = (
            db.query(Company)
            .filter(
                Company.id == company_id
            )
            .first()
        )

        if company is None:
            return {
                "success": False,
                "error": (
                    f"Company {company_id} not found."
                ),
            }

        # -------------------------------------------------
        # FIND DECISION MAKER
        # -------------------------------------------------

        decision_maker = (
            OutreachService.get_decision_maker(
                db=db,
                company_id=company_id,
                decision_maker_id=decision_maker_id,
            )
        )

        if decision_maker is None:
            return {
                "success": False,
                "error": (
                    "No suitable decision maker "
                    "was found."
                ),
            }

        # -------------------------------------------------
        # VALIDATE EMAIL
        # -------------------------------------------------

        if not decision_maker.email:
            return {
                "success": False,
                "error": (
                    "Decision maker does not have "
                    "an email address."
                ),
            }

        # -------------------------------------------------
        # FIND NBA
        # -------------------------------------------------

        nba = (
            OutreachService.get_pending_nba(
                db=db,
                company_id=company_id,
            )
        )

        if nba is None:
            return {
                "success": False,
                "error": (
                    "No pending Next Best Action "
                    "exists for this company."
                ),
            }

        # -------------------------------------------------
        # DUPLICATE CAMPAIGN CHECK
        # -------------------------------------------------

        existing_campaign = (
            OutreachService.find_existing_pending_campaign(
                db=db,
                company_id=company_id,
                decision_maker_id=decision_maker.id,
            )
        )

        if existing_campaign is not None:

            existing_queue = (
                db.query(EmailQueue)
                .filter(
                    EmailQueue.campaign_id
                    == existing_campaign.id,
                    EmailQueue.status
                    == "Pending",
                )
                .first()
            )

            return {
                "success": True,
                "version": OutreachService.VERSION,
                "duplicate": True,
                "message": (
                    "Pending outreach already exists."
                ),
                "company": {
                    "id": company.id,
                    "name": company.name,
                },
                "decision_maker": {
                    "id": decision_maker.id,
                    "full_name": (
                        decision_maker.full_name
                    ),
                    "title": decision_maker.title,
                    "email": decision_maker.email,
                },
                "next_best_action": {
                    "id": nba.id,
                    "action_type": nba.action_type,
                    "priority": nba.priority,
                    "recommended_within_hours": (
                        nba.recommended_within_hours
                    ),
                },
                "campaign": {
                    "id": existing_campaign.id,
                    "name": (
                        existing_campaign.campaign_name
                    ),
                    "status": existing_campaign.status,
                },
                "email_queue": {
                    "id": (
                        existing_queue.id
                        if existing_queue
                        else None
                    ),
                    "status": (
                        existing_queue.status
                        if existing_queue
                        else None
                    ),
                },
            }

        # -------------------------------------------------
        # BUILD CAMPAIGN CONTENT
        # -------------------------------------------------

        subject = (
            OutreachService.build_subject(
                company=company,
                decision_maker=decision_maker,
                nba=nba,
            )
        )

        message = (
            OutreachService.build_message(
                company=company,
                decision_maker=decision_maker,
                nba=nba,
            )
        )

        if not campaign_name:
            campaign_name = (
                f"LUIP Outreach - {company.name}"
            )

        # -------------------------------------------------
        # CREATE CAMPAIGN
        # -------------------------------------------------

        campaign = OutreachCampaign(
            company_id=company.id,
            decision_maker_id=decision_maker.id,
            campaign_name=campaign_name,
            campaign_type="Email",
            subject=subject,
            message=message,
            status="Draft",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        db.add(campaign)

        # -------------------------------------------------
        # FLUSH CAMPAIGN
        # -------------------------------------------------

        db.flush()

        # -------------------------------------------------
        # CREATE EMAIL QUEUE
        # -------------------------------------------------

        email_queue = EmailQueue(
            company_id=company.id,
            decision_maker_id=decision_maker.id,
            campaign_id=campaign.id,
            smtp_provider=settings.SMTP_DEFAULT_PROVIDER,
            recipient_email=decision_maker.email,
            recipient_name=decision_maker.full_name,
            subject=subject,
            body=message,
            priority=nba.priority,
            status="Pending",
            retry_count=0,
            max_retries=5,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        db.add(email_queue)

        # -------------------------------------------------
        # COMMIT
        # -------------------------------------------------

        try:

            db.commit()

        except Exception as exc:

            db.rollback()

            return {
                "success": False,
                "error": (
                    "Unable to create outreach."
                ),
                "detail": str(exc),
            }

        # -------------------------------------------------
        # REFRESH
        # -------------------------------------------------

        db.refresh(campaign)
        db.refresh(email_queue)

        # -------------------------------------------------
        # RETURN
        # -------------------------------------------------

        return {
            "success": True,
            "version": OutreachService.VERSION,
            "duplicate": False,

            "company": {
                "id": company.id,
                "name": company.name,
                "website": company.website,
                "industry": company.industry,
            },

            "decision_maker": {
                "id": decision_maker.id,
                "full_name": (
                    decision_maker.full_name
                ),
                "title": decision_maker.title,
                "department": (
                    decision_maker.department
                ),
                "email": decision_maker.email,
                "verified": decision_maker.verified,
            },

            "next_best_action": {
                "id": nba.id,
                "action_type": nba.action_type,
                "priority": nba.priority,
                "recommended_within_hours": (
                    nba.recommended_within_hours
                ),
                "explanation": nba.explanation,
                "ai_reasoning": nba.ai_reasoning,
            },

            "campaign": {
                "id": campaign.id,
                "name": campaign.campaign_name,
                "type": campaign.campaign_type,
                "subject": campaign.subject,
                "message": campaign.message,
                "status": campaign.status,
            },

            "email_queue": {
                "id": email_queue.id,
                "recipient_email": (
                    email_queue.recipient_email
                ),
                "recipient_name": (
                    email_queue.recipient_name
                ),
                "subject": email_queue.subject,
                "priority": email_queue.priority,
                "status": email_queue.status,
            },
        }