"""A wrapper around a user's email, so that they may send emails.

Required environment variables:
 - GMAIL_API_KEY: Your API key for accessing your Gmail
    - See: https://support.google.com/mail/answer/185833?hl=en

Author: Aidan McNay
Date: September 16th, 2024
"""

import os
import smtplib
import ssl
from typing import Optional, Self

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ------------------------------------------------------------------------
# GmailMailer
# ------------------------------------------------------------------------


class Mailer:
    """An object-oriented abstraction for sending an email through Gmail.

    Note: mailers for other services could be derived by changing the SMTP
    server they connect to
    """

    def __init__(self: Self, sender_email: str) -> None:
        """Log into the Gmail SMTP server.

        Args:
            sender_email (str): The email to send emails from
        """
        self.email = sender_email

        self.smtp_client = smtplib.SMTP_SSL(
            "smtp.gmail.com", 465, context=ssl.create_default_context()
        )
        self.smtp_client.login(self.email, os.environ["GMAIL_API_KEY"])

    def send(
        self: Self,
        recipient: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        text_type: str = "plain",
    ) -> None:
        """Send an email.

        Args:
            recipient (str): The email of the recipient
            subject (str): The subject of the email
            body (str): The body of the email
            cc (Optional[str]): The email to cc, if any
            bcc (Optional[str]): The email to bcc, if any
            text_type (str): The type of text we're sending, either 'plain'
              or 'html'. Defaults to 'plain'
        """
        if text_type not in ("plain", "html"):
            raise Exception(f"Invalid text type: {text_type}")

        msg = MIMEMultipart()
        msg["From"] = self.email
        msg["To"] = recipient
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = cc
        if bcc:
            msg["Bcc"] = bcc
        msg.attach(MIMEText(body, text_type))

        try:
            self.smtp_client.sendmail(self.email, recipient, msg.as_string())
        except Exception:
            self.smtp_client = smtplib.SMTP_SSL(
                "smtp.gmail.com", 465, context=ssl.create_default_context()
            )
            self.smtp_client.login(self.email, os.environ["GMAIL_API_KEY"])
            self.smtp_client.sendmail(self.email, recipient, msg.as_string())
