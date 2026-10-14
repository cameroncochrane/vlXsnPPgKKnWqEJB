# Contains the backend logic regarding Telegram and email notifications/updates

# Base imports:
import asyncio
import telegram
import mailtrap as mt
import os
import requests

# Custom imports:


# ===================
# Telegram:

# First time set-up:
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set.")

# Retrieving the id of the recipient account(s):
#   url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
#   response = requests.get(url)
#   print(response.json())
# Important output of this should be id = 8958267173 (CC account)
chat_id = 8958267173 

def send_telegram_message(chat_id, message):
    """
    Send Telegram notification.
    (To be used after each trade execuition with details of the trade)
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


# ===================
# Mailtrap:

MAILTRAP_API_TOKEN = os.getenv("MAILTRAP_API_TOKEN")


def send_email(subject, message, recipient_email="cochranecameron1@gmail.com"):
    """
    Send email notification
    (To be used to send a weekly email with a summary of the portfolio, the positions, and the trades executed that week)
    """
    if not MAILTRAP_API_TOKEN:
        raise RuntimeError("MAILTRAP_API_TOKEN environment variable is not set.")

    # Sanitize token and common header fields to avoid Unicode in HTTP headers
    def _sanitize_header_value(val: str) -> str:
        """Return a header-safe string encoded in latin-1 to stop "UnicodeEncodeError" messages.

        This replaces common “smart” quotes and dashes with ASCII equivalents and
        ensures any remaining non-latin-1 characters are replaced with '?'.

        Example:
            _sanitize_header_value('“Hello”') -> '"Hello"'
        """
        if not isinstance(val, str):
            return val

        replacements = {
            '\u2018': "'",
            '\u2019': "'",
            '\u201c': '"',
            '\u201d': '"',
            '\u2013': '-',
            '\u2014': '-',
            '\u2026': '...',
        }
        for k, v in replacements.items():
            val = val.replace(k, v)
        try:
            val.encode('latin-1')
            return val
        except UnicodeEncodeError:
            # Replace any remaining non-latin-1 characters with '?'
            return val.encode('latin-1', errors='replace').decode('latin-1')

    token = _sanitize_header_value(MAILTRAP_API_TOKEN).strip("\"'")

    mail = mt.Mail(
        sender=mt.Address(email="hello@demomailtrap.co", name=_sanitize_header_value("Mailtrap Test")),
        to=[mt.Address(email=recipient_email)],
        subject=_sanitize_header_value(subject),
        text=message,
        category=_sanitize_header_value("Integration Test"),
    )

    client = mt.MailtrapClient(token=token)
    return client.send(mail)


if __name__ == "__main__":
    send_email(
        subject="Mailtrap Test 2",
        message="I'm sorry I still can't do that Dave",
        recipient_email="cochranecameron1@gmail.com",
    )
