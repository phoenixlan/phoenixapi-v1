from operator import truediv
import os
import json
import pika
import threading

from phoenixRest.services.pubsub import PubsubService
from phoenixRest.services.pubsub.rabbitmq.thread import RabbitmqThread

import logging
log = logging.getLogger(__name__)

class RabbitMQService(PubsubService):
    def __init__(self, service_manager):
        super().__init__(service_manager)

        host = os.environ['RABBITMQ_HOST']

        username = os.environ['RABBITMQ_USER']
        password = os.environ['RABBITMQ_PASSWORD']

        credentials = pika.PlainCredentials(username, password)

        log.info("Starting RabbitMQ thread")

        self._thread = RabbitmqThread(host, credentials)
        self._thread.daemon = True
        self._thread.start()
    
    def ensure_task_queue(self, queue_name):
        self._thread.ensure_queue(queue_name)
    
    def send_task(self, channel, payload):
        self._thread.send_message(channel, payload)


