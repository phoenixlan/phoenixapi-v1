import logging
log = logging.getLogger(__name__)

from phoenixRest.services.service import Service

class PositionNotificationService(Service):
    def __init__(self, service_manager) -> None:
        super().__init__(service_manager)
        service_manager.get_service('pubsub').ensure_task_queue('position_changes')
    
    def notify_user_position_mappings_changed(self, user):
        log.info(f"Notifying pubsub that {user.uuid}'s positions have changed")
        self.service_manager.get_service('pubsub').send_task('position_changes', {
            "user_uuid": str(user.uuid)
        })

class NoopPositionNotificationService(Service):
    def __init__(self, service_manager) -> None:
        super().__init__(service_manager)
    
    def notify_user_position_mappings_changed(self, user):
        log.info(f"NOOP: {user.uuid}'s positions have changed")


