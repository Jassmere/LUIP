import smtplib
import ssl
from datetime import datetime, UTC, timedelta
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.config import settings

# ---------------------------------------------------------
# Model registration
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
    records through the configured SMTP provider.

    Supported providers:
        default
        gmail
        outlook
        zoho

    This service does NOT create campaigns and does NOT
    generate outreach content.

    Pipeline:

        EmailQueue
            ↓
        EmailService
            ↓
        Selected SMTP Provider
            ↓
        Recipient

    Live transmission requires BOTH:

        EMAIL_DRY_RUN=False
        EMAIL_LIVE_ENABLED=True

    Provider selection:

        EmailQueue.smtp_provider
            ↓
        SMTP_DEFAULT_PROVIDER
            ↓
        Selected SMTP configuration

    Live safety:

        EMAIL_LIVE_MAX_BATCH is a hard ceiling on the number
        of live queue entries that may be processed during one
        process_pending_queue() call.

    Version: 1.1.0
    """

    VERSION = "1.1.0"

    SUPPORTED_PROVIDERS = {
        "default",
        "gmail",
        "outlook",
        "zoho",
    }

    # =====================================================
    # PROVIDER NORMALIZATION
    # =====================================================

    @staticmethod
    def normalize_provider(
        provider: str | None,
    ) -> str:
        """
        Normalize an SMTP provider name.

        Missing or blank values use the configured default
        provider.

        Unknown providers raise ValueError rather than
        silently selecting an unintended mailbox.
        """

        if provider is None:
            provider = getattr(
                settings,
                "SMTP_DEFAULT_PROVIDER",
                "default",
            )

        provider = str(provider).strip().lower()

        if not provider:
            provider = getattr(
                settings,
                "SMTP_DEFAULT_PROVIDER",
                "default",
            )

            provider = str(provider).strip().lower()

        if provider not in EmailService.SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported SMTP provider: {provider}. "
                f"Supported providers: "
                f"{', '.join(sorted(EmailService.SUPPORTED_PROVIDERS))}."
            )

        return provider

    # =====================================================
    # PROVIDER CONFIGURATION
    # =====================================================

    @staticmethod
    def get_provider_config(
        provider: str | None = None,
    ) -> dict:
        """
        Return the SMTP configuration for a provider.

        When provider is omitted, the configured
        SMTP_DEFAULT_PROVIDER is resolved.

        The explicit "default" provider uses the original
        SMTP_* fields for backward compatibility.
        """

        provider = EmailService.normalize_provider(
            provider
        )

        # -------------------------------------------------
        # GMAIL
        # -------------------------------------------------

        if provider == "gmail":
            return {
                "provider": "gmail",
                "host": getattr(
                    settings,
                    "GMAIL_SMTP_HOST",
                    "smtp.gmail.com",
                ),
                "port": getattr(
                    settings,
                    "GMAIL_SMTP_PORT",
                    587,
                ),
                "username": getattr(
                    settings,
                    "GMAIL_SMTP_USERNAME",
                    "",
                ),
                "password": getattr(
                    settings,
                    "GMAIL_SMTP_PASSWORD",
                    "",
                ),
                "from_email": getattr(
                    settings,
                    "GMAIL_SMTP_FROM_EMAIL",
                    "",
                ),
                "from_name": getattr(
                    settings,
                    "GMAIL_SMTP_FROM_NAME",
                    "Lawyered Up",
                ),
                "use_tls": bool(
                    getattr(
                        settings,
                        "GMAIL_SMTP_USE_TLS",
                        True,
                    )
                ),
                "use_ssl": bool(
                    getattr(
                        settings,
                        "GMAIL_SMTP_USE_SSL",
                        False,
                    )
                ),
                "timeout": int(
                    getattr(
                        settings,
                        "GMAIL_SMTP_TIMEOUT",
                        30,
                    )
                ),
            }

        # -------------------------------------------------
        # OUTLOOK
        # -------------------------------------------------

        if provider == "outlook":
            return {
                "provider": "outlook",
                "host": getattr(
                    settings,
                    "OUTLOOK_SMTP_HOST",
                    "smtp.office365.com",
                ),
                "port": getattr(
                    settings,
                    "OUTLOOK_SMTP_PORT",
                    587,
                ),
                "username": getattr(
                    settings,
                    "OUTLOOK_SMTP_USERNAME",
                    "",
                ),
                "password": getattr(
                    settings,
                    "OUTLOOK_SMTP_PASSWORD",
                    "",
                ),
                "from_email": getattr(
                    settings,
                    "OUTLOOK_SMTP_FROM_EMAIL",
                    "",
                ),
                "from_name": getattr(
                    settings,
                    "OUTLOOK_SMTP_FROM_NAME",
                    "Lawyered Up",
                ),
                "use_tls": bool(
                    getattr(
                        settings,
                        "OUTLOOK_SMTP_USE_TLS",
                        True,
                    )
                ),
                "use_ssl": bool(
                    getattr(
                        settings,
                        "OUTLOOK_SMTP_USE_SSL",
                        False,
                    )
                ),
                "timeout": int(
                    getattr(
                        settings,
                        "OUTLOOK_SMTP_TIMEOUT",
                        30,
                    )
                ),
            }

        # -------------------------------------------------
        # ZOHO
        # -------------------------------------------------

        if provider == "zoho":
            return {
                "provider": "zoho",
                "host": getattr(
                    settings,
                    "ZOHO_SMTP_HOST",
                    "smtp.zoho.com",
                ),
                "port": getattr(
                    settings,
                    "ZOHO_SMTP_PORT",
                    587,
                ),
                "username": getattr(
                    settings,
                    "ZOHO_SMTP_USERNAME",
                    "",
                ),
                "password": getattr(
                    settings,
                    "ZOHO_SMTP_PASSWORD",
                    "",
                ),
                "from_email": getattr(
                    settings,
                    "ZOHO_SMTP_FROM_EMAIL",
                    "",
                ),
                "from_name": getattr(
                    settings,
                    "ZOHO_SMTP_FROM_NAME",
                    "Lawyered Up",
                ),
                "use_tls": bool(
                    getattr(
                        settings,
                        "ZOHO_SMTP_USE_TLS",
                        True,
                    )
                ),
                "use_ssl": bool(
                    getattr(
                        settings,
                        "ZOHO_SMTP_USE_SSL",
                        False,
                    )
                ),
                "timeout": int(
                    getattr(
                        settings,
                        "ZOHO_SMTP_TIMEOUT",
                        30,
                    )
                ),
            }

        # -------------------------------------------------
        # DEFAULT / LEGACY SMTP
        # -------------------------------------------------

        return {
            "provider": "default",
            "host": getattr(
                settings,
                "SMTP_HOST",
                "",
            ),
            "port": getattr(
                settings,
                "SMTP_PORT",
                587,
            ),
            "username": getattr(
                settings,
                "SMTP_USERNAME",
                "",
            ),
            "password": getattr(
                settings,
                "SMTP_PASSWORD",
                "",
            ),
            "from_email": getattr(
                settings,
                "SMTP_FROM_EMAIL",
                "",
            ),
            "from_name": getattr(
                settings,
                "SMTP_FROM_NAME",
                "Lawyered Up",
            ),
            "use_tls": bool(
                getattr(
                    settings,
                    "SMTP_USE_TLS",
                    True,
                )
            ),
            "use_ssl": bool(
                getattr(
                    settings,
                    "SMTP_USE_SSL",
                    False,
                )
            ),
            "timeout": int(
                getattr(
                    settings,
                    "SMTP_TIMEOUT",
                    30,
                )
            ),
        }

    # =====================================================
    # CONFIGURATION
    # =====================================================

    @staticmethod
    def is_configured(
        provider: str | None = None,
    ) -> bool:
        """
        Return True when the selected SMTP provider has the
        minimum configuration required for live sending.

        Backward compatibility:

        When provider is omitted, the original SMTP_* fields
        are checked directly.

        When provider is explicitly supplied, the
        provider-specific configuration is checked.
        """

        try:
            if provider is None:
                config = {
                    "host": getattr(
                        settings,
                        "SMTP_HOST",
                        "",
                    ),
                    "port": getattr(
                        settings,
                        "SMTP_PORT",
                        587,
                    ),
                    "username": getattr(
                        settings,
                        "SMTP_USERNAME",
                        "",
                    ),
                    "password": getattr(
                        settings,
                        "SMTP_PASSWORD",
                        "",
                    ),
                    "from_email": getattr(
                        settings,
                        "SMTP_FROM_EMAIL",
                        "",
                    ),
                }

            else:
                config = EmailService.get_provider_config(
                    provider
                )

        except ValueError:
            return False

        return bool(
            config["host"]
            and config["port"]
            and config["username"]
            and config["password"]
            and config["from_email"]
        )

    @staticmethod
    def is_dry_run() -> bool:
        """
        Return whether live email transmission is disabled.
        """

        return bool(
            getattr(
                settings,
                "EMAIL_DRY_RUN",
                True,
            )
        )

    @staticmethod
    def is_live_enabled() -> bool:
        """
        Return whether explicit operator authorization for
        live email transmission has been enabled.
        """

        return bool(
            getattr(
                settings,
                "EMAIL_LIVE_ENABLED",
                False,
            )
        )

    @staticmethod
    def can_send_live(
        provider: str | None = None,
    ) -> bool:
        """
        Return True only when live transmission is authorized
        and the selected SMTP provider is configured.
        """

        return (
            not EmailService.is_dry_run()
            and EmailService.is_live_enabled()
            and EmailService.is_configured(
                provider
            )
        )

    # =====================================================
    # LIVE SAFETY
    # =====================================================

    @staticmethod
    def get_live_max_batch() -> int:
        """
        Return the configured maximum number of live emails
        permitted during one process_pending_queue() call.

        The safety ceiling fails closed:

        - Missing value defaults to 1.
        - None defaults to 1.
        - Invalid values default to 1.
        - Values below 1 default to 1.

        A value of 1 is deliberately conservative because
        live email transmission is an externally visible
        operation.
        """

        try:
            max_batch = int(
                getattr(
                    settings,
                    "EMAIL_LIVE_MAX_BATCH",
                    1,
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            return 1

        if max_batch < 1:
            return 1

        return max_batch

    # =====================================================
    # TIME / SCHEDULING
    # =====================================================

    @staticmethod
    def utc_now() -> datetime:
        """
        Return the current timezone-aware UTC timestamp.
        """

        return datetime.now(UTC)

    @staticmethod
    def is_scheduled_for_future(
        email_queue: EmailQueue,
    ) -> bool:
        """
        Return True when the queue entry has a scheduled_for
        timestamp later than the current UTC time.
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
            updated_at = email_queue.updated_at

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
                if email_queue.status == "Pending":
                    db.refresh(
                        email_queue
                    )

        return recovered

    # =====================================================
    # SMTP CONNECTION
    # =====================================================

    @staticmethod
    def create_smtp_connection(
        provider: str | None = None,
    ):
        """
        Create and authenticate an SMTP connection for the
        selected provider.

        Supports:

            SMTP over SSL
            STARTTLS
            Plain SMTP when TLS is disabled
        """

        config = EmailService.get_provider_config(
            provider
        )

        host = config["host"]
        port = config["port"]
        username = config["username"]
        password = config["password"]
        use_ssl = config["use_ssl"]
        use_tls = config["use_tls"]
        timeout = config["timeout"]

        if not host:
            raise ValueError(
                f"SMTP host is not configured for "
                f"provider '{config['provider']}'."
            )

        if not port:
            raise ValueError(
                f"SMTP port is not configured for "
                f"provider '{config['provider']}'."
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

        Provider behaviour:

        - If smtp_provider is explicitly assigned, the
          selected provider configuration is used.

        - If smtp_provider is missing, the original legacy
          SMTP_* configuration is used.
        """

        provider = getattr(
            email_queue,
            "smtp_provider",
            None,
        )

        if provider is None or not str(provider).strip():

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

            if not from_email:
                raise ValueError(
                    "SMTP From email is not configured."
                )

        else:

            config = EmailService.get_provider_config(
                provider
            )

            from_name = config["from_name"]
            from_email = config["from_email"]

            if not from_email:
                raise ValueError(
                    f"SMTP From email is not configured "
                    f"for provider '{config['provider']}'."
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

        No database changes are performed here.

        Provider routing:

        - "default", missing, or blank smtp_provider uses
          the legacy zero-argument SMTP path.

        - Explicit provider values such as "gmail",
          "outlook", or "zoho" are passed to both SMTP
          configuration validation and SMTP connection.
        """

        if not email_queue.recipient_email:
            return {
                "success": False,
                "error": (
                    "Recipient email address is missing."
                ),
            }

        requested_provider = getattr(
            email_queue,
            "smtp_provider",
            None,
        )

        explicit_provider = (
            requested_provider is not None
            and str(
                requested_provider
            ).strip().lower()
            not in {
                "",
                "default",
            }
        )

        try:
            provider = EmailService.normalize_provider(
                requested_provider
            )

        except ValueError as exc:
            return {
                "success": False,
                "error": str(exc),
            }

        if EmailService.is_dry_run():
            return {
                "success": True,
                "dry_run": True,
                "provider": provider,
                "message": (
                    "Email transmission skipped "
                    "because EMAIL_DRY_RUN is enabled."
                ),
            }

        if not EmailService.is_live_enabled():
            return {
                "success": False,
                "live_blocked": True,
                "provider": provider,
                "error": (
                    "Live email transmission is disabled. "
                    "Set EMAIL_LIVE_ENABLED=True only after "
                    "SMTP configuration and pilot approval "
                    "have been completed."
                ),
            }

        if explicit_provider:

            if not EmailService.is_configured(
                provider
            ):
                return {
                    "success": False,
                    "provider": provider,
                    "error": (
                        "SMTP is not configured."
                    ),
                }

        else:

            if not EmailService.is_configured():
                return {
                    "success": False,
                    "provider": provider,
                    "error": (
                        "SMTP is not configured."
                    ),
                }

        smtp = None

        try:

            if explicit_provider:
                smtp = (
                    EmailService.create_smtp_connection(
                        provider
                    )
                )

            else:
                smtp = (
                    EmailService.create_smtp_connection()
                )

            message = (
                EmailService.build_email_message(
                    email_queue
                )
            )

            smtp.send_message(
                message
            )

            return {
                "success": True,
                "dry_run": False,
                "provider": provider,
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
                "provider": provider,
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

        retry_count = (
            email_queue.retry_count
            if email_queue.retry_count is not None
            else 0
        )

        if retry_count < max_retries:
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

        Live authorization is checked before changing the
        queue status to Processing.
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

        if (
            not EmailService.is_dry_run()
            and not EmailService.is_live_enabled()
        ):
            return {
                "success": False,
                "processed": False,
                "live_blocked": True,
                "queue_id": email_queue.id,
                "reason": (
                    "Live email transmission is disabled."
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

        email_queue.status = "Processing"

        email_queue.updated_at = (
            EmailService.utc_now()
        )

        db.commit()

        db.refresh(
            email_queue
        )

        result = EmailService.send_email(
            email_queue
        )

        if result.get("success"):

            if result.get("dry_run"):

                email_queue.status = "Pending"

                email_queue.updated_at = (
                    EmailService.utc_now()
                )

                db.commit()

                db.refresh(
                    email_queue
                )

                return {
                    "success": True,
                    "processed": True,
                    "dry_run": True,
                    "queue_id": email_queue.id,
                    "provider": result.get(
                        "provider"
                    ),
                    "message": result.get(
                        "message"
                    ),
                }

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

            db.refresh(
                email_queue
            )

            return {
                "success": True,
                "processed": True,
                "dry_run": False,
                "queue_id": email_queue.id,
                "provider": result.get(
                    "provider"
                ),
                "message": (
                    "Email queue entry sent."
                ),
                "campaign_id": (
                    email_queue.campaign_id
                ),
                "campaign_status": (
                    "Sent"
                    if email_queue.campaign_id
                    else None
                ),
            }

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

        db.refresh(
            email_queue
        )

        terminal_failure = (
            email_queue.retry_count
            >= max_retries
        )

        return {
            "success": False,
            "processed": True,
            "dry_run": False,
            "queue_id": email_queue.id,
            "provider": result.get(
                "provider"
            ),
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

        The caller-supplied limit controls the normal maximum
        number of records selected.

        When live email execution is authorized, the
        EMAIL_LIVE_MAX_BATCH setting is a HARD SAFETY CEILING.

        Therefore:

            effective_limit =
                min(caller_limit, EMAIL_LIVE_MAX_BATCH)

        This ensures that a caller cannot accidentally bypass
        the live-email safety ceiling by supplying a larger
        processing limit.

        Queue processing also:

        - recovers stale Processing entries
        - excludes future-scheduled entries
        - prioritises Critical, High, Medium, then Normal
        - respects the caller-supplied limit
        - enforces EMAIL_LIVE_MAX_BATCH during live execution
        - preserves retry handling
        """

        if limit is None or limit <= 0:
            limit = 10

        # -------------------------------------------------
        # GLOBAL LIVE AUTHORIZATION GATE
        # -------------------------------------------------

        live_execution = (
            not EmailService.is_dry_run()
            and EmailService.is_live_enabled()
        )

        if (
            not EmailService.is_dry_run()
            and not EmailService.is_live_enabled()
        ):
            return {
                "success": False,
                "version": EmailService.VERSION,
                "dry_run": False,
                "live_blocked": True,
                "processed": 0,
                "sent": 0,
                "failed": 0,
                "dry_run_count": 0,
                "stale_recovered": 0,
                "scheduled_skipped": 0,
                "results": [],
                "error": (
                    "Live email transmission is disabled. "
                    "Set EMAIL_LIVE_ENABLED=True only after "
                    "SMTP configuration and pilot approval "
                    "have been completed."
                ),
            }

        # -------------------------------------------------
        # DETERMINE EFFECTIVE PROCESSING CEILING
        # -------------------------------------------------

        effective_limit = limit

        if live_execution:
            live_max_batch = (
                EmailService.get_live_max_batch()
            )

            effective_limit = min(
                limit,
                live_max_batch,
            )

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
        # LOAD QUEUE
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
        # COUNT FUTURE-SCHEDULED ENTRIES
        # -------------------------------------------------

        scheduled_entries = [
            entry
            for entry in queue_entries
            if EmailService.is_scheduled_for_future(
                entry
            )
        ]

        scheduled_skipped = len(
            scheduled_entries
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

        # -------------------------------------------------
        # PRIORITY ORDER
        # -------------------------------------------------

        priority_order = {
            "Critical": 1,
            "High": 2,
            "Medium": 3,
            "Normal": 4,
        }

        executable_entries.sort(
            key=lambda entry: (
                priority_order.get(
                    entry.priority,
                    99,
                ),
                entry.created_at,
            )
        )

        # -------------------------------------------------
        # APPLY EFFECTIVE SAFETY LIMIT
        # -------------------------------------------------

        queue_entries = executable_entries[
            :effective_limit
        ]

        results = []

        # -------------------------------------------------
        # PROCESS EXECUTABLE ENTRIES
        # -------------------------------------------------

        for email_queue in queue_entries:

            result = (
                EmailService.process_queue_entry(
                    db=db,
                    email_queue=email_queue,
                )
            )

            results.append(
                result
            )

        # -------------------------------------------------
        # RESULT COUNTS
        # -------------------------------------------------

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

        # -------------------------------------------------
        # FINAL RESULT
        # -------------------------------------------------

        return {
            "success": True,
            "version": EmailService.VERSION,
            "dry_run": EmailService.is_dry_run(),
            "processed": len(results),
            "sent": sent_count,
            "failed": failed_count,
            "dry_run_count": dry_run_count,
            "stale_recovered": stale_recovered,
            "scheduled_skipped": scheduled_skipped,
            "results": results,
        }