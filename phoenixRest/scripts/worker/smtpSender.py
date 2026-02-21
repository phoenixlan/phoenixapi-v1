from typing import List
import os
import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText

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

            for to_address in to_addresses:
                msg = EmailMessage()
                msg["From"] = from_address
                msg["To"] = to_address
                msg["Subject"] = subject
                msg.preamble = """
This e-mail is best viewed in a modern e-mail client. Here is a preview of what you are missing:

""" + body

                html_body = MIMEText(body, 'html')
                msg.attach(html_body)

                s.send_message(msg)