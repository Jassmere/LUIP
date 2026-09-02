from pathlib import Path

path = Path("app/services/email_service.py")

text = path.read_text(encoding="utf-8")

old = """        if not EmailService.is_configured():
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
"""

new = """        if not EmailService.is_configured(provider):
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
                EmailService.create_smtp_connection(provider)
            )
"""

if old not in text:
    raise SystemExit(
        "TARGET BLOCK NOT FOUND. FILE WAS NOT CHANGED."
    )

text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")

print("Provider-routing fix applied successfully.")
