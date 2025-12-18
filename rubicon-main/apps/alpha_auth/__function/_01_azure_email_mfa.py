
# import os
# import sys
# sys.path.append("/www/alpha/")
# import django
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
# django.setup()

import random

import logging
import traceback
import datetime

from azure.communication.email import EmailClient
from alpha.settings import (
    VITE_OP_TYPE,
    VITE_COUNTRY,
    AZURE_EMAIL_ENDPOINT,
    AZURE_EMAIL_API_KEY
)

from django.core.cache import cache

from apps.alpha_auth.models import Alpha_User

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("system_email_alert")


def generate_6_digit_code():
    return random.randint(100000, 999999)

def make_mfa_code(
    recipient
):
    """
    Send a process error alert with both HTML and plain text versions.

    Args:
        recipient (str): Email address of the recipient

    Returns:
        bool: Success status
    """

    # Basic info that goes in every alert
    timestamp = (
        datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z (%Z)")
    )
    environment = VITE_OP_TYPE
    locale = VITE_COUNTRY

    # Create subject
    subject = "Your Rubicon Admin Verification Code"
    header = "Verification Code"

    mfa_code = generate_6_digit_code()

    plain_content = _create_plain_text_alert(
        header,
        mfa_code
    )
    html_content = _create_html_alert(
        header,
        mfa_code
    )

    cache_key = f"mfa_code_{recipient}"
    cache.set(cache_key, mfa_code, timeout=300)  # Store for 5 minutes

    # Send to all recipient
    success = _send_email(recipient, subject, plain_content, html_content)

    return success


def _create_plain_text_alert(
    header, mfa_code
):
    """Create the plain text version of the alert."""

    # Create both versions of the email content

    content = f"""{header}

Your verification code is {mfa_code}

Please enter this code to complete your sign-in process.
This code will expire in 5 minutes.

If you did not request this code, please ignore this email.

Thank you,
"""
    return content


def _create_html_alert(
    header, mfa_code
):
    """Create the HTML version of the alert."""

    # Build context rows for HTML table
    return f"""
<!DOCTYPE html>
<html>
  <body style="font-family: Arial, sans-serif; background: #f9f9f9; padding: 24px;">
    <div style="max-width: 480px; margin: auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px #eee; padding: 32px;">
      <h2 style="color: #1976d2; margin-top: 0;">{header}</h2>
      <p>Hello,</p>
      <p>Your verification code is:</p>
      <div style="font-size: 2em; font-weight: bold; letter-spacing: 8px; color: #1976d2; margin: 24px 0;">
        {mfa_code}
      </div>
      <p>Please enter this code to complete your sign-in process.<br>
      This code will expire in <b>5 minutes</b>.</p>
      <p style="color: #888; font-size: 0.95em;">
        If you did not request this code, please ignore this email.
      </p>
      <hr style="border: none; border-top: 1px solid #eee; margin: 32px 0 16px 0;">
      <div style="color: #888; font-size: 0.95em;">Thank you,<br>The Rubicon Team</div>
    </div>
  </body>
</html>"""


def get_sender_address():
    """Get the sender email address from environment variables."""
    if VITE_OP_TYPE == "STG":
        return f"DoNotReply@stg-notify-{VITE_COUNTRY.lower()}.samsunggenai.com"
    elif VITE_OP_TYPE == "PRD":
        return f"DoNotReply@notify-{VITE_COUNTRY.lower()}.samsunggenai.com"
    else:
        return "DoNotReply@dev-notify.samsunggenai.com"


def _send_email(recipient, subject, plain_content, html_content):
    """Send the actual email using Azure Communication Services."""
    try:
        if not AZURE_EMAIL_ENDPOINT or not AZURE_EMAIL_API_KEY:
            logger.error(
                "Azure email configuration missing. Check environment variables."
            )
            return False

        connection_string = (
            f"endpoint={AZURE_EMAIL_ENDPOINT};accesskey={AZURE_EMAIL_API_KEY}"
        )
        client = EmailClient.from_connection_string(connection_string)

        message = {
            "senderAddress": get_sender_address(),
            "recipients": {"to": [{"address": recipient}]},
            "content": {
                "subject": subject,
                "plainText": plain_content,
                "html": html_content,
            },
        }

        poller = client.begin_send(message)
        result = poller.result()
        logger.info(
            f"Email sent successfully: Azure ID {result["id"]} | Status: {result["status"]}"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        logger.debug(traceback.format_exc())
        return False


# Example usage:
if __name__ == "__main__":
    # Simple usage
    import time
    email_address = 'wishfree76@gmail.com'
    email_address = 'dae-il.yang@pwc.com'
    start_time = time.time()
    make_mfa_code(
        email_address
    )
    print(f"Execution time: {time.time() - start_time:.2f} seconds")
