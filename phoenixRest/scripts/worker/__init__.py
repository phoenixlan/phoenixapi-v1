import argparse
import sys
import pika
import os
import requests
import json
import argparse

from .mailgunSender import MailgunSender
from .smtpSender import SmtpSender
from .gmailSender import GmailSender

import logging
logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)



from pyramid.paster import bootstrap, setup_logging


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'config_uri',
        help='Configuration file, e.g., development.ini',
    )
    parser.add_argument("mail_provider", choices=["mailgun", "smtp", "gmail"])
    return parser.parse_args(argv[1:])


def main(argv=sys.argv):
    args = parse_args(argv)
    setup_logging(args.config_uri)
    env = bootstrap(args.config_uri)


    # Worker logic
    match args.mail_provider:
        case "mailgun":
            sender = MailgunSender()
        case "smtp":
            sender = SmtpSender()
        case "gmail":
            sender = GmailSender()

    username = os.environ['RABBITMQ_USER']
    password = os.environ['RABBITMQ_PASSWORD']

    credentials = pika.PlainCredentials(username, password)

    connection = pika.BlockingConnection(pika.ConnectionParameters(os.environ.get('RABBITMQ_HOST'), credentials=credentials))
    channel = connection.channel()

    listen_topic = os.environ['RABBITMQ_LISTEN_TOPIC']
    channel.queue_declare(queue=listen_topic, durable=True)

    def callback(ch, method, properties, body):
        log.info("Received %r" % body)
        try:
            json_body = json.loads(body)
            sender.send_email(json_body["from"], json_body["to"], json_body["subject"], json_body["html"])
            log.info("Done sending e-mail")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as err:
            log.warn("Failed to send e-mail: %s" % err)

    channel.basic_consume(queue=listen_topic,
                        auto_ack=False,
                        on_message_callback=callback)

    log.info("Listening for events")
    channel.start_consuming()