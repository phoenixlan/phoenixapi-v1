import os
import requests
from typing import List

import logging
log = logging.getLogger(__name__)


class MailgunSender:
    def __init__(self):
        self.mailgun_domain = os.environ["MAILGUN_DOMAIN"]
        self.api_domain = os.environ["MAILGUN_API"]
        self.api_key = os.environ["MAILGUN_API_KEY"]

    def send_email(self, from_address: str, to_addresses: List[str], subject: str, body: str):
        requests.post(
            "https://%s/v3/%s/messages" % (self.api_domain, self.mailgun_domain),
            auth=("api", self.api_key),
            data={
                "from": from_address,
                "to": to_addresses,
                "subject": subject,
                "html": body
            }
        )
