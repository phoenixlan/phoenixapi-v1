import os
import json
import pika

from phoenixRest.services.pubsub import PubsubService

import logging
log = logging.getLogger(__name__)

class RabbitMQService(PubsubService):
    def __init__(self, service_manager):
        super().__init__(service_manager)

        host = os.environ['RABBITMQ_HOST']

        username = os.environ['RABBITMQ_USER']
        password = os.environ['RABBITMQ_PASSWORD']

        credentials = pika.PlainCredentials(username, password)

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host, credentials=credentials))
        self.channel = self.connection.channel()
        
        log.info("Set up rabbitmq")
    
    def ensure_task_queue(self, queue_name):
        self.channel.queue_declare(queue=queue_name, durable=True)
    
    def send_task(self, channel, payload):
        self.channel.basic_publish(
            exchange='',
            routing_key=channel,
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ))


