from typing import List
import os
import smtplib
from email.message import EmailMessage

import logging
log = logging.getLogger(__name__)


class SmtpSender:
    def __init__(self):
        self.smtp_server = os.environ["SMTP_SERVER"]
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER")
        self.smtp_password = os.environ.get("SMTP_PASSWORD")

    def send_email(self, from_address: str, to_addresses: List[str], subject: str, body: str):
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as s:
            s.starttls()
            if self.smtp_user and self.smtp_password:
                s.login(self.smtp_user, self.smtp_password)

            if not isinstance(to_addresses, list):
                raise ValueError("bad to addresses")

            for to_address in to_addresses:
                msg = EmailMessage()

                log.info(f"from: {from_address}")
                log.info(f"to: {to_address}")
                log.info(f"subject: {subject}")
                log.info(f"body: {body}")

                msg["From"] = from_address
                msg["To"] = to_address
                msg["Subject"] = subject
                msg.set_content(body, subtype='html')

                s.send_message(msg)