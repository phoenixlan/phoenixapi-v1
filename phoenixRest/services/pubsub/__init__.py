from phoenixRest.services.service import Service

class PubsubService(Service):
    def __init__(self, service_manager):
        super().__init__(service_manager)

    def ensure_task_queue(self, queue_name):
        raise RuntimeError("ensure_task_queue not implemented")

    def send_task(self, channel, payload):
        raise RuntimeError("Unable to send task to pubsub: send_task not implemented")