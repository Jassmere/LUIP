from email.message import EmailMessage
from types import SimpleNamespace


from app.services.email_service import EmailService


class FakeSMTP:
    def __init__(self):
        self.sent_messages = []
        self.quit_called = False

    def send_message(
        self,
        message,
    ):
        self.sent_messages.append(message)

    def quit(self):
        self.quit_called = True


def test_send_email_routes_explicit_zoho_provider(
    monkeypatch,
):
    fake_smtp = FakeSMTP()

    configured_providers = []
    connection_providers = []

    monkeypatch.setattr(
        EmailService,
        "is_dry_run",
        staticmethod(
            lambda: False
        ),
    )

    monkeypatch.setattr(
        EmailService,
        "is_live_enabled",
        staticmethod(
            lambda: True
        ),
    )

    def fake_is_configured(
        provider=None,
    ):
        configured_providers.append(
            provider
        )
        return True

    monkeypatch.setattr(
        EmailService,
        "is_configured",
        staticmethod(
            fake_is_configured
        ),
    )

    def fake_create_smtp_connection(
        provider=None,
    ):
        connection_providers.append(
            provider
        )
        return fake_smtp

    monkeypatch.setattr(
        EmailService,
        "create_smtp_connection",
        staticmethod(
            fake_create_smtp_connection
        ),
    )

    message = EmailMessage()

    message["From"] = (
        "sender@example.com"
    )

    message["To"] = (
        "recipient@example.com"
    )

    message["Subject"] = (
        "Provider routing test"
    )

    message.set_content(
        "Provider routing test."
    )

    monkeypatch.setattr(
        EmailService,
        "build_email_message",
        staticmethod(
            lambda email_queue: message
        ),
    )

    email_queue = SimpleNamespace(
        recipient_email=(
            "recipient@example.com"
        ),
        recipient_name="Test Recipient",
        smtp_provider="zoho",
    )

    result = EmailService.send_email(
        email_queue
    )

    assert result["success"] is True

    assert result["dry_run"] is False

    assert result["provider"] == "zoho"

    assert result["recipient"] == (
        "recipient@example.com"
    )

    assert configured_providers == [
        "zoho",
    ]

    assert connection_providers == [
        "zoho",
    ]

    assert len(
        fake_smtp.sent_messages
    ) == 1

    assert (
        fake_smtp.sent_messages[0]
        is message
    )

    assert fake_smtp.quit_called is True