import threading
from tkinter import E
import pika
import json

import logging
log = logging.getLogger(__name__)

pika_logger = logging.getLogger("pika")
pika_logger.setLevel(logging.DEBUG)

class RabbitmqThread(threading.Thread):

    def __init__(self, host, credentials):
        super().__init__()

        self._host = host
        self._credentials = credentials
        
        self._lock = threading.Lock()

        self._connection = None
        self._channel = None

        self._running = False

        self._should_stop = False

        self._active_queues = ['position-updates']
        # Used to communicate between the threads
        self._pending_queues = []
        self._pending_messages = []

    # inter-thread api
    def ensure_queue(self, queuename):
        with self._lock:
            if queuename in self._active_queues or queuename in self._pending_queues:
                raise RuntimeError("Tried to register queue name that already exists: %s" % queuename)
            self._pending_queues.append(queuename)
            # TODO signal the thread
            if self._channel is not None:
                self._connection.ioloop.add_callback_threadsafe(self._poll)
            
    
    def send_message(self, channel, payload):
        if not self._running:
            raise RuntimeError("Tried to write a message to RabbitMQ but we have no connection - failing so we don't promise sending something that ends up never being sent")

        if type(payload) is not dict:
            raise RuntimeError("Provided message is not a dictionary: %s" % payload)
        
        try:
            json.dumps(payload)
        except:
            raise RuntimeError("Payload is not json-able: %s" % payload)

        log.debug(f"Submitting message to {channel}")
        with self._lock:
            if channel not in self._active_queues and channel not in self._pending_queues:
                raise RuntimeError("Tried to send a message to a queue that is not registered")
            self._pending_messages.append((channel, payload))
            if self._channel is not None:
                log.debug("Asking for a poll")
                self._connection.ioloop.add_callback_threadsafe(self._poll)
    
    def _connect(self):
        return pika.SelectConnection(
            pika.ConnectionParameters(self._host, credentials=self._credentials), 
            on_open_callback=self._on_connect, 
            on_close_callback=self._on_close,
            on_open_error_callback=self._on_open_error,
        )

    # Callbacks to do stuff in the rabbitmq thread
    def _poll(self):
        with self._lock:
            for queue in self._pending_queues:
                self._channel.queue_declare(queue=queue, durable=True, callback=self._on_queue_declared)
                self._active_queues.append(queue)
            self._pending_queues.clear()

            for message in self._pending_messages:
                log.debug(f"Sending message to {message[0]}")
                self._channel.basic_publish( 
                    exchange='',
                    routing_key=message[0],
                    body=json.dumps(message[1]),
                    properties=pika.BasicProperties(
                        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                    ))


    def run(self):
        """Main function that handles rabbitmq in a separate thread"""
        log.info("Started RabbitMQ thread")
        # Ensure that if someone called send_message or ensure_queue during connection, things are handled properly
        while not self._should_stop:
            # Set up the connection
            self._connection = self._connect()

            log.warning("Starting IOLoop")
            self._connection.ioloop.start()
            log.warning("IOLoop stopped!")

        log.warning("RabbitMQ iothread is done!")

    def _on_open_error(self, _unused_conn, err):
        log.error(f"Failed to open RabbitMQ connection, restarting in 5 seconds: {err}")
        self._running = False
        self._connection.ioloop.call_later(5, self._connection.ioloop.stop)

    def _on_connect(self, connection):
        log.info(f"Rabbitmq connection is open: {self._connection} vs {connection}")
        self._connection = connection
        self._connection.channel(on_open_callback=self._on_channel_open)

    def _on_channel_open(self, channel):
        self._channel = channel
        self._channel.add_on_close_callback(self._on_channel_close)
        log.info("RabbitMQ channel opened")
        self._running = True
        # Make sure _poll() is called once the channel is open
        self._connection.ioloop.add_callback(self._poll)

    def _on_queue_declared(self, frame):
        log.info(f"queue declared: {frame}")

    def _on_channel_close(self, channel, exc):
        log.error(f"Rabbitmq channel is closing!: {exc}")

    def _on_close(self, connection, exception):
        log.warning("Rabbitmq connection is closing")
        self._running = False
        self._connection.ioloop.call_later(5, self._connection.ioloop.stop)
