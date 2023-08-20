import pika
import os
import json

from phoenixRest.services.mail import MailService

import logging
log = logging.getLogger(__name__)

class PubsubMailService(MailService):
    def __init__(self, service_manager, settings):
        super().__init__(service_manager)
        log.info("Set up PubSub Mail service")
        service_manager.get_service('pubsub').ensure_task_queue('email')

        self.from_address = settings['api.automated_email_address']
        self.sender = "Phoenix LAN"
    
    def _send_mail_impl(self, to: str, subject: str, body: str):
        data = {"from": "%s<%s>" % (self.sender, self.from_address),
                "to": [to],
                "subject": subject,
                "html": body}

        self.service_manager.get_service('pubsub').send_task('email', data)
        

