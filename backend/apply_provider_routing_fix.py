from pathlib import Path


FILE = Path("app/services/email_service.py")


OLD = '''    @staticmethod
    def send_email(
        email_queue: EmailQueue,
    ) -> dict:
        """
        Send one EmailQueue record.

        No database changes are performed here.

        Provider compatibility:

        is_configured() and create_smtp_connection() are
        intentionally called without arguments because the
        existing LUIP tests monkeypatch these methods with
        zero-argument callables.
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
'''


NEW = '''    @staticmethod
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
'''


def main() -> None:
    if not FILE.exists():
        raise SystemExit(
            f"ERROR: File does not exist: {FILE}"
        )

    source = FILE.read_text(
        encoding="utf-8"
    )

    occurrence_count = source.count(OLD)

    if occurrence_count != 1:
        raise SystemExit(
            "ERROR: Expected exactly one frozen "
            "send_email() implementation was not found. "
            f"Found {occurrence_count} matches. "
            "No changes were made."
        )

    updated = source.replace(
        OLD,
        NEW,
        1,
    )

    FILE.write_text(
        updated,
        encoding="utf-8",
        newline="",
    )

    print(
        "Provider routing fix applied successfully."
    )


if __name__ == "__main__":
    main()