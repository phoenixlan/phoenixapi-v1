from typing import List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2 import service_account
from googleapiclient import discovery
import base64
import os

import logging
log = logging.getLogger(__name__)

GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']


class GmailSender:
    def __init__(self):
        self.credentials_file = os.environ['GOOGLE_CREDENTIALS_FILE']
        self.sender_address = os.environ['GMAIL_SENDER_ADDRESS']

        # Validate credentials on startup
        self._build_service(self.sender_address)
        log.info(f"Gmail sender initialized for {self.sender_address}")

    def _build_service(self, sender_address: str):
        creds = service_account.Credentials.from_service_account_file(
            self.credentials_file, scopes=GMAIL_SCOPES
        )
        delegated_creds = creds.with_subject(sender_address)
        return discovery.build('gmail', 'v1', credentials=delegated_creds)

    def send_email(self, from_address: str, to_addresses: List[str], subject: str, body: str):
        service = self._build_service(from_address)

        for to_address in to_addresses:
            msg = MIMEMultipart('alternative')
            msg["From"] = from_address
            msg["To"] = to_address
            msg["Subject"] = subject

            msg.attach(MIMEText(body, 'html'))

            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()

            send_message = (
                service.users()
                .messages()
                .send(userId="me", body={'raw': raw_message})
                .execute()
            )
            log.info(f"Email sent to {to_address}, message id: {send_message.get('id')}")