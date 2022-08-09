from . import MailProvider

import os

import requests

import logging
log = logging.getLogger(__name__)

class MailgunMailProvider(MailProvider):
    def __init__(self):
        self.domain = os.environ["MAILGUN_DOMAIN"]
        self.mailgun_api = os.environ["MAILGUN_API"]
        self.api_key = os.environ["MAILGUN_API_KEY"]
        self.from_address = os.environ["MAILGUN_FROM_EMAIL"]
        self.sender = "Phoenix LAN"

        log.info("Setting up mailgun for %s against %s" % (self.domain, self.mailgun_api))
        super().__init__()

    def _send_mail_impl(self, to: str, subject: str, body: str):
        requests.post(
            "https://%s/v3/%s/messages" % (self.mailgun_api, self.domain),
            auth=("api", self.api_key),
            data={"from": "%s<info@%s>" % (self.sender, self.domain),
                "to": [to],
                "subject": subject,
                "html": body})
