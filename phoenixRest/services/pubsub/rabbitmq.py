import os
import json
import pika
import threading

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

        self.connection = pika.SelectConnection(pika.ConnectionParameters(host, credentials=credentials), on_open_callback=self._on_open)
        self.channel = None

        self.thread = threading.Thread(target=self._rabbitmq_thread, daemon=True)
        self.thread.start()
        
        log.info("Set up rabbitmq: %s" % self)
    
    def _on_open(self, _):
        log.info("Rabbitmq connection is open")
        self.connection.channel(on_open_callback=self._on_channel_open)
    
    def _on_channel_open(self, channel):
        self.channel = channel
        self.channel.add_on_close_callback(channel)
        log.info("RabbitMQ channel opened")
    
    def _on_channel_close(self, channel):
        log.warning("RabbitMQ channel closed!")

    def _rabbitmq_thread(self):
        log.info("RabbitMQ ioloop thread started")
        self.connection.ioloop.start()
        log.info("RabbitMQ ioloop thread finished?")
    
    def ensure_task_queue(self, queue_name):
        log.info("Ensuring task queue on %s" % self)
        self.channel.queue_declare(queue=queue_name, durable=True)
    
    def send_task(self, channel, payload):
        self.channel.basic_publish(
            exchange='',
            routing_key=channel,
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ))


