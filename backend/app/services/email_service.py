import smtplib
import ssl

from datetime import datetime, UTC, timedelta
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.config import settings

# ---------------------------------------------------------
# Model registration
# ---------------------------------------------------------
#
# Register the models referenced by EmailQueue relationships
# before SQLAlchemy initializes the EmailQueue mapper.
#
# This is especially important when the outreach scheduler
# is executed directly rather than through the full FastAPI
# application startup sequence.
# ---------------------------------------------------------

from app.models.company import Company
from app.models.decision_maker import DecisionMaker
from app.models.next_best_action import NextBestAction
from app.models.outreach_campaign import OutreachCampaign
from app.models.email_queue import EmailQueue


class EmailService:
    """
    LUIP Email Execution Service.

    Responsible for transmitting prepared EmailQueue
    records through SMTP.

    This service does NOT create campaigns and does NOT
    generate outreach content.

    Pipeline:

        EmailQueue
            ↓
        EmailService
            ↓
        SMTP
            ↓
        Recipient

    Version: 1.0.0
    """

    VERSION = "1.0.0"

    # =====================================================
    # CONFIGURATION
    # =====================================================

    @staticmethod
    def is_configured() -> bool:
        """
        Return True when the minimum SMTP configuration
        required for live sending is available.
        """

        return bool(
            getattr(settings, "SMTP_HOST", "")
            and getattr(settings, "SMTP_PORT", None)
            and getattr(settings, "SMTP_USERNAME", "")
            and getattr(settings, "SMTP_PASSWORD", "")
            and getattr(settings, "SMTP_FROM_EMAIL", "")
        )

    @staticmethod
    def is_dry_run() -> bool:
        """
        Return whether live email transmission is disabled.

        Dry-run defaults to True so the LUIP scheduler cannot
        accidentally transmit email before the pilot operator
        explicitly enables live sending.
        """

        return bool(
            getattr(
                settings,
                "EMAIL_DRY_RUN",
                True,
            )
        )

    # =====================================================
    # TIME / SCHEDULING
    # =====================================================

    @staticmethod
    def utc_now() -> datetime:
        """
        Return the current timezone-aware UTC timestamp.

        Centralising this call makes scheduling and stale
        processing logic easier to test.
        """

        return datetime.now(UTC)

    @staticmethod
    def is_scheduled_for_future(
        email_queue: EmailQueue,
    ) -> bool:
        """
        Return True when the queue entry has a scheduled_for
        timestamp that is later than the current UTC time.

        A queue entry without scheduled_for is immediately
        executable.
        """

        scheduled_for = email_queue.scheduled_for

        if scheduled_for is None:
            return False

        if scheduled_for.tzinfo is None:
            scheduled_for = scheduled_for.replace(
                tzinfo=UTC
            )

        return scheduled_for > EmailService.utc_now()

    @staticmethod
    def recover_stale_processing(
        db: Session,
        stale_minutes: int = 30,
    ) -> int:
        """
        Recover EmailQueue records that have remained in
        Processing state longer than the configured stale
        threshold.

        Recovered entries are returned to Pending so the
        scheduler can safely retry them.

        Returns the number of recovered records.
        """

        if stale_minutes is None or stale_minutes <= 0:
            stale_minutes = 30

        cutoff = (
            EmailService.utc_now()
            - timedelta(
                minutes=stale_minutes
            )
        )

        processing_entries = (
            db.query(EmailQueue)
            .filter(
                EmailQueue.status == "Processing"
            )
            .all()
        )

        recovered = 0

        for email_queue in processing_entries:

            updated_at = (
                email_queue.updated_at
            )

            if updated_at is None:
                is_stale = True

            else:

                if updated_at.tzinfo is None:
                    updated_at = updated_at.replace(
                        tzinfo=UTC
                    )

                is_stale = (
                    updated_at <= cutoff
                )

            if not is_stale:
                continue

            email_queue.status = "Pending"

            email_queue.error_message = (
                "Recovered stale Processing "
                "queue entry."
            )

            email_queue.updated_at = (
                EmailService.utc_now()
            )

            recovered += 1

        if recovered:
            db.commit()

            for email_queue in processing_entries:

                if (
                    email_queue.status
                    == "Pending"
                ):
                    db.refresh(email_queue)

        return recovered

    # =====================================================
    # SMTP CONNECTION
    # =====================================================

    @staticmethod
    def create_smtp_connection():
        """
        Create and authenticate an SMTP connection.

        Supports:

            SMTP_USE_TLS=True
                STARTTLS

        and:

            SMTP_USE_SSL=True
                implicit SSL

        The connection is returned to the caller and must
        be closed by the caller.
        """

        host = settings.SMTP_HOST
        port = settings.SMTP_PORT
        username = settings.SMTP_USERNAME
        password = settings.SMTP_PASSWORD

        use_ssl = bool(
            getattr(
                settings,
                "SMTP_USE_SSL",
                False,
            )
        )

        use_tls = bool(
            getattr(
                settings,
                "SMTP_USE_TLS",
                True,
            )
        )

        timeout = int(
            getattr(
                settings,
                "SMTP_TIMEOUT",
                30,
            )
        )

        context = ssl.create_default_context()

        if use_ssl:

            server = smtplib.SMTP_SSL(
                host=host,
                port=port,
                timeout=timeout,
                context=context,
            )

        else:

            server = smtplib.SMTP(
                host=host,
                port=port,
                timeout=timeout,
            )

            server.ehlo()

            if use_tls:

                server.starttls(
                    context=context
                )

                server.ehlo()

        if username and password:

            server.login(
                username,
                password,
            )

        return server

    # =====================================================
    # MESSAGE
    # =====================================================

    @staticmethod
    def build_email_message(
        email_queue: EmailQueue,
    ) -> EmailMessage:
        """
        Convert an EmailQueue record into an EmailMessage.
        """

        from_name = getattr(
            settings,
            "SMTP_FROM_NAME",
            "Lawyered Up",
        )

        from_email = getattr(
            settings,
            "SMTP_FROM_EMAIL",
            "",
        )

        message = EmailMessage()

        message["From"] = (
            f"{from_name} <{from_email}>"
        )

        message["To"] = (
            email_queue.recipient_email
        )

        message["Subject"] = (
            email_queue.subject
        )

        message.set_content(
            email_queue.body
        )

        return message

    # =====================================================
    # SEND ONE EMAIL
    # =====================================================

    @staticmethod
    def send_email(
        email_queue: EmailQueue,
    ) -> dict:
        """
        Send one EmailQueue record.

        Returns a structured result.

        No database changes are performed here.
        """

        if not email_queue.recipient_email:

            return {
                "success": False,
                "error": (
                    "Recipient email address is missing."
                ),
            }

        # -------------------------------------------------
        # DRY RUN SAFETY
        # -------------------------------------------------

        if EmailService.is_dry_run():

            return {
                "success": True,
                "dry_run": True,
                "message": (
                    "Email transmission skipped "
                    "because EMAIL_DRY_RUN is enabled."
                ),
            }

        # -------------------------------------------------
        # SMTP CONFIGURATION
        # -------------------------------------------------

        if not EmailService.is_configured():

            return {
                "success": False,
                "error": (
                    "SMTP is not configured."
                ),
            }

        smtp = None

        try:

            message = (
                EmailService.build_email_message(
                    email_queue
                )
            )

            smtp = (
                EmailService.create_smtp_connection()
            )

            smtp.send_message(
                message
            )

            return {
                "success": True,
                "dry_run": False,
                "message": (
                    "Email sent successfully."
                ),
                "recipient": (
                    email_queue.recipient_email
                ),
            }

        except Exception as exc:

            return {
                "success": False,
                "error": str(exc),
            }

        finally:

            if smtp is not None:

                try:
                    smtp.quit()

                except Exception:
                    pass

    # =====================================================
    # CAMPAIGN SYNCHRONIZATION
    # =====================================================

    @staticmethod
    def synchronize_campaign_success(
        db: Session,
        email_queue: EmailQueue,
    ) -> None:
        """
        Synchronize a successfully delivered email with
        its associated OutreachCampaign.

        Delivery means the campaign email was transmitted
        successfully. It does not mean the recipient opened,
        clicked, replied, or booked a meeting.
        """

        campaign_id = (
            email_queue.campaign_id
        )

        if campaign_id is None:
            return

        campaign = (
            db.query(OutreachCampaign)
            .filter(
                OutreachCampaign.id
                == campaign_id
            )
            .first()
        )

        if campaign is None:
            return

        campaign.status = "Sent"

        campaign.sent_at = (
            email_queue.sent_at
            or EmailService.utc_now()
        )

        campaign.updated_at = (
            EmailService.utc_now()
        )

    # =====================================================
    # CAMPAIGN FAILURE SYNCHRONIZATION
    # =====================================================

    @staticmethod
    def synchronize_campaign_failure(
        db: Session,
        email_queue: EmailQueue,
    ) -> None:
        """
        Synchronize a terminal email delivery failure with
        the associated campaign.

        A campaign is marked Failed only when the queue entry
        reaches its maximum retry count.
        """

        campaign_id = (
            email_queue.campaign_id
        )

        if campaign_id is None:
            return

        campaign = (
            db.query(OutreachCampaign)
            .filter(
                OutreachCampaign.id
                == campaign_id
            )
            .first()
        )

        if campaign is None:
            return

        max_retries = (
            email_queue.max_retries
            if email_queue.max_retries is not None
            else 5
        )

        if (
            email_queue.retry_count
            < max_retries
        ):
            return

        campaign.status = "Failed"

        campaign.updated_at = (
            EmailService.utc_now()
        )

    # =====================================================
    # PROCESS QUEUE ENTRY
    # =====================================================

    @staticmethod
    def process_queue_entry(
        db: Session,
        email_queue: EmailQueue,
    ) -> dict:
        """
        Process one EmailQueue record.

        Status transitions:

            Pending
                ↓
            Processing
                ↓
            Sent

        OR:

            Processing
                ↓
            Failed

        Failed messages can be retried while retry_count
        remains below max_retries.

        Future scheduled messages are not processed.
        """

        if email_queue.status not in {
            "Pending",
            "Failed",
        }:

            return {
                "success": False,
                "processed": False,
                "reason": (
                    f"Queue status "
                    f"'{email_queue.status}' "
                    "is not executable."
                ),
            }

        # -------------------------------------------------
        # FUTURE SCHEDULE PROTECTION
        # -------------------------------------------------

        if EmailService.is_scheduled_for_future(
            email_queue
        ):

            return {
                "success": True,
                "processed": False,
                "scheduled": True,
                "queue_id": email_queue.id,
                "reason": (
                    "Email is scheduled for "
                    "a future time."
                ),
            }

        if email_queue.retry_count is None:
            email_queue.retry_count = 0

        max_retries = (
            email_queue.max_retries
            if email_queue.max_retries is not None
            else 5
        )

        if email_queue.retry_count >= max_retries:

            return {
                "success": False,
                "processed": False,
                "reason": (
                    "Maximum retry count reached."
                ),
            }

        # -------------------------------------------------
        # MARK PROCESSING
        # -------------------------------------------------

        email_queue.status = "Processing"

        email_queue.updated_at = (
            EmailService.utc_now()
        )

        db.commit()
        db.refresh(email_queue)

        # -------------------------------------------------
        # SEND
        # -------------------------------------------------

        result = EmailService.send_email(
            email_queue
        )

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        if result.get("success"):

            # -------------------------------------------------
            # DRY RUN
            # -------------------------------------------------

            if result.get("dry_run"):

                # Dry-run must never falsely mark an email
                # as delivered.
                email_queue.status = "Pending"

                email_queue.updated_at = (
                    EmailService.utc_now()
                )

                db.commit()
                db.refresh(email_queue)

                return {
                    "success": True,
                    "processed": True,
                    "dry_run": True,
                    "queue_id": email_queue.id,
                    "message": result.get(
                        "message"
                    ),
                }

            # -------------------------------------------------
            # LIVE SEND SUCCESS
            # -------------------------------------------------

            email_queue.status = "Sent"

            email_queue.sent_at = (
                EmailService.utc_now()
            )

            email_queue.error_message = None

            email_queue.updated_at = (
                EmailService.utc_now()
            )

            EmailService.synchronize_campaign_success(
                db=db,
                email_queue=email_queue,
            )

            db.commit()
            db.refresh(email_queue)

            return {
                "success": True,
                "processed": True,
                "dry_run": False,
                "queue_id": email_queue.id,
                "message": (
                    "Email queue entry sent."
                ),
                "campaign_id": (
                    email_queue.campaign_id
                ),
                "campaign_status": "Sent"
                if email_queue.campaign_id
                else None,
            }

        # -------------------------------------------------
        # FAILURE
        # -------------------------------------------------

        email_queue.status = "Failed"

        email_queue.retry_count += 1

        email_queue.error_message = (
            result.get("error")
            or "Unknown email delivery error."
        )

        email_queue.updated_at = (
            EmailService.utc_now()
        )

        EmailService.synchronize_campaign_failure(
            db=db,
            email_queue=email_queue,
        )

        db.commit()
        db.refresh(email_queue)

        terminal_failure = (
            email_queue.retry_count
            >= max_retries
        )

        return {
            "success": False,
            "processed": True,
            "dry_run": False,
            "queue_id": email_queue.id,
            "retry_count": (
                email_queue.retry_count
            ),
            "max_retries": max_retries,
            "terminal_failure": terminal_failure,
            "error": (
                email_queue.error_message
            ),
        }

    # =====================================================
    # PROCESS PENDING QUEUE
    # =====================================================

    @staticmethod
    def process_pending_queue(
        db: Session,
        limit: int = 10,
    ) -> dict:
        """
        Process pending email queue entries.

        The limit prevents one scheduler cycle from
        accidentally sending an uncontrolled number of
        emails.

        Priority order:

            Critical
            High
            Medium
            Normal

        Future scheduled messages remain untouched.

        Stale Processing entries are recovered before
        queue execution.
        """

        if limit is None or limit <= 0:
            limit = 10

        priority_order = {
            "Critical": 1,
            "High": 2,
            "Medium": 3,
            "Normal": 4,
        }

        # -------------------------------------------------
        # RECOVER STALE PROCESSING RECORDS
        # -------------------------------------------------

        stale_recovered = (
            EmailService.recover_stale_processing(
                db=db,
                stale_minutes=30,
            )
        )

        # -------------------------------------------------
        # LOAD EXECUTABLE QUEUE
        # -------------------------------------------------

        queue_entries = (
            db.query(EmailQueue)
            .filter(
                EmailQueue.status.in_(
                    [
                        "Pending",
                        "Failed",
                    ]
                )
            )
            .order_by(
                EmailQueue.created_at.asc()
            )
            .all()
        )

        # -------------------------------------------------
        # REMOVE FUTURE-SCHEDULED ENTRIES
        # -------------------------------------------------

        executable_entries = [
            entry
            for entry in queue_entries
            if not EmailService.is_scheduled_for_future(
                entry
            )
        ]

        executable_entries.sort(
            key=lambda entry: (
                priority_order.get(
                    entry.priority,
                    99,
                ),
                entry.created_at,
            )
        )

        queue_entries = executable_entries[
            :limit
        ]

        results = []

        skipped_scheduled = max(
            0,
            len(
                [
                    entry
                    for entry in queue_entries
                    if EmailService.is_scheduled_for_future(
                        entry
                    )
                ]
            ),
        )

        for email_queue in queue_entries:

            result = (
                EmailService.process_queue_entry(
                    db=db,
                    email_queue=email_queue,
                )
            )

            results.append(result)

        sent_count = sum(
            1
            for result in results
            if (
                result.get("success")
                and not result.get("dry_run")
                and result.get("processed")
            )
        )

        failed_count = sum(
            1
            for result in results
            if (
                not result.get("success")
                and result.get("processed")
            )
        )

        dry_run_count = sum(
            1
            for result in results
            if result.get("dry_run")
        )

        return {
            "success": True,
            "version": EmailService.VERSION,
            "dry_run": EmailService.is_dry_run(),
            "processed": len(results),
            "sent": sent_count,
            "failed": failed_count,
            "dry_run_count": dry_run_count,
            "stale_recovered": stale_recovered,
            "scheduled_skipped": skipped_scheduled,
            "results": results,
        }