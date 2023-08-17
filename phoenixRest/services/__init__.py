import os

from phoenixRest.services.mail.pubsub_mail import PubsubMailService
from phoenixRest.services.mail import MailService

from phoenixRest.services.pubsub import PubsubService
from phoenixRest.services.pubsub.rabbitmq import RabbitMQService

import logging
log = logging.getLogger(__name__)

class ServiceManager():
    def __init__(self):
        self.services = {}
    
    def register_service(self, name, handler):
        if name in self.services.keys():
            raise RuntimeError("Unable to register service %s - already existed" % name)

        self.services[name] = handler

    def get_service(self, name):
        if name not in self.services:
            raise RuntimeError("Attempted to get service that doesn't exist: %s" % name)
        
        return self.services[name]

def setup_service_manager(settings):
    log.info(settings)

    service_manager = ServiceManager()

    # pubsub
    pubsub = PubsubService(service_manager)
    if "service.pubsub.provider" in settings:
        if settings['service.pubsub.provider'] == "rabbitmq":
            log.info("Using RabbitMQ for pubsub")
            pubsub = RabbitMQService(service_manager)

    service_manager.register_service("pubsub", pubsub)

    # Mail
    mail_provider = MailService(service_manager)
    if "service.mail.provider" in settings:
        if settings["service.mail.provider"] == "pubsub":
            log.info("Using pubsub for sending mails")
            mail_provider = PubsubMailService(service_manager, settings)
    
    service_manager.register_service("email", mail_provider)

    return service_manager
    

