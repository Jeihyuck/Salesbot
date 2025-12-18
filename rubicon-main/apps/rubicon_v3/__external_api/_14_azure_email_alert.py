import sys

sys.path.append("/www/alpha/")

import logging
import traceback
import datetime

from azure.communication.email import EmailClient
from alpha.settings import (
    VITE_OP_TYPE,
    VITE_COUNTRY,
    AZURE_EMAIL_ENDPOINT,
    AZURE_EMAIL_API_KEY,
    AZURE_EMAIL_RECIPIENTS,
    AZURE_EMAIL_JAEIL_RECIPIENTS,
    AZURE_EMAIL_DEVCRA_RECIPIENTS,
    AZURE_EMAIL_CSBOT_RECIPIENTS,
    AZURE_EMAIL_SPRINKLR_RECIPIENTS,
    AZURE_EMAIL_DOTCOMSEARCH_RECIPIENTS,
)

from apps.rubicon_v3.__function.definitions import channels

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("system_email_alert")


def send_process_error_alert(
    error_message,
    error_type,
    recipients=None,
    error_traceback=None,
    context_data=None,
):
    """
    Send a process error alert with both HTML and plain text versions.

    Args:
        error_message (str): Brief error description
        error_type (str): Type of error (e.g., "validation_error", "pipeline_error")
        recipients (list or str, optional): List of email addresses or a single address
        error_traceback (str, optional): Full error traceback
        context_data (dict, optional): Additional context (session_id, user_id, etc.)

    Returns:
        bool: Success status
    """
    if not recipients:
        recipients = AZURE_EMAIL_RECIPIENTS

    if isinstance(recipients, str):
        recipients = [recipients]

    # Basic info that goes in every alert
    timestamp = (
        datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z (%Z)")
    )
    environment = VITE_OP_TYPE
    locale = VITE_COUNTRY

    # Create subject
    subject = None
    header = None
    if error_type == "validation_error":
        subject = f"Validation Error ({environment}): {str(error_traceback)}{'...' if len(error_traceback) > 50 else ''}"
        header = "INPUT VALIDATION ERROR ALERT"
        if context_data and context_data.get("Channel"):
            if context_data["Channel"] in [
                channels.SAMSUNGPLUS,
                channels.AITOOL,
                channels.STAR,
            ]:
                recipients.extend(AZURE_EMAIL_JAEIL_RECIPIENTS)
            elif context_data["Channel"] in [
                channels.AIBOT,
                channels.AIBOT2,
                channels.EXECUTIVE,
                channels.FAMILYNET,
                channels.RETAIL_KX,
                channels.SMARTTHINGS,
                channels.STAR_DA,
                channels.STAR_VD,
                channels.UT_BU,
                channels.UT_CX,
                channels.UT_DA,
                channels.UT_DPC,
                channels.UT_ETC,
                channels.UT_EXT,
                channels.UT_FNET,
                channels.UT_MX,
                channels.UT_ST,
                channels.UT_VD,
            ]:
                recipients.extend(AZURE_EMAIL_DEVCRA_RECIPIENTS)
            elif context_data["Channel"] in [channels.CSBOT]:
                recipients.extend(AZURE_EMAIL_CSBOT_RECIPIENTS)
            elif context_data["Channel"] in [
                channels.DOTCOMCHAT,
                channels.SPRINKLR,
            ]:
                recipients.extend(AZURE_EMAIL_SPRINKLR_RECIPIENTS)
            elif context_data["Channel"] in [channels.DOTCOMSEARCH]:
                recipients.extend(AZURE_EMAIL_DOTCOMSEARCH_RECIPIENTS)

    else:
        subject = f"Process Error ({environment}): {error_message[:50]}{'...' if len(error_message) > 50 else ''}"
        header = "PROCESS ERROR ALERT"

    # Create both versions of the email content
    plain_content = _create_plain_text_alert(
        header,
        error_message,
        error_traceback,
        timestamp,
        environment,
        locale,
        context_data,
    )
    html_content = _create_html_alert(
        header,
        error_message,
        error_traceback,
        timestamp,
        environment,
        locale,
        context_data,
    )

    # Send to all recipients
    success = _send_email(recipients, subject, plain_content, html_content)

    return success


def _create_plain_text_alert(
    header, error_message, error_traceback, timestamp, environment, locale, context_data
):
    """Create the plain text version of the alert."""
    content = f"""{header}

Error: {error_message}

SYSTEM INFO:
- Timestamp: {timestamp}
- Environment: {environment}
- Locale: {locale}
"""

    if context_data:
        content += "\nCONTEXT:\n"
        for key, value in context_data.items():
            content += f"- {key}: {value}\n"

    if error_traceback:
        content += f"\nERROR TRACEBACK:\n{error_traceback}"

    return content


def _create_html_alert(
    header, error_message, error_traceback, timestamp, environment, locale, context_data
):
    """Create the HTML version of the alert."""

    # Build context rows for HTML table
    context_rows = ""
    if context_data:
        for key, value in context_data.items():
            context_rows += f"""
                <div class="info-row">
                    <span class="label">{key}:</span>
                    <span class="value">{value}</span>
                </div>"""

    return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.5;
            color: #e8e9ea;
            margin: 0;
            padding: 20px;
            background-color: #2d2d2d;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: #3a3a3a;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            padding: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 18px;
        }}
        .content {{
            padding: 20px;
        }}
        .error-message {{
            background: #e74c3c;
            border: 1px solid #c0392b;
            color: white;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-weight: bold;
        }}
        .info-section {{
            margin-bottom: 20px;
        }}
        .info-section h3 {{
            color: #3498db;
            font-size: 14px;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}
        .info-row {{
            display: flex;
            padding: 5px 0;
            border-bottom: 1px solid #555555;
        }}
        .info-row:last-child {{
            border-bottom: none;
        }}
        .label {{
            font-weight: bold;
            color: #bdc3c7;
            width: 120px;
            flex-shrink: 0;
        }}
        .value {{
            color: #ecf0f1;
            font-family: monospace;
        }}
        .traceback {{
            background: #2d2d2d;
            border: 1px solid #4a4a4a;
            border-radius: 4px;
            padding: 15px;
            font-family: monospace;
            font-size: 12px;
            white-space: pre-wrap;
            overflow-x: auto;
            color: #ecf0f1;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{header}</h1>
        </div>
        <div class="content">
            <div class="error-message">
                {error_message}
            </div>
            
            <div class="info-section">
                <h3>System Information</h3>
                <div class="info-row">
                    <span class="label">Timestamp:</span>
                    <span class="value">{timestamp}</span>
                </div>
                <div class="info-row">
                    <span class="label">Environment:</span>
                    <span class="value">{environment}</span>
                </div>
                <div class="info-row">
                    <span class="label">Locale:</span>
                    <span class="value">{locale}</span>
                </div>
                {context_rows}
            </div>
            
            {f'''<div class="info-section">
                <h3>Error Details</h3>
                <div class="traceback">{error_traceback}</div>
            </div>''' if error_traceback else ''}
        </div>
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


def _send_email(recipients, subject, plain_content, html_content):
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
            "recipients": {
                "to": [{"address": "rubicon@samsung.com"}],
                "bcc": [{"address": addr} for addr in recipients],
            },
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

    start_time = time.time()
    send_process_error_alert(
        error_message="This is a test error message for Azure email alert.",
        error_type="validation_error",
        recipients="jaewon0907@gmail.com",
        error_traceback="Traceback (most recent call last):  File...",
        context_data={
            "Session ID": "sess_123",
            "User ID": "user_456",
            "Channel": "DEV Debug",
        },
    )
    print(f"Execution time: {time.time() - start_time:.2f} seconds")
