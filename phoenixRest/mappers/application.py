from phoenixRest.models.crew.application import ApplicationState
from phoenixRest.mappers.user import map_user_with_secret_fields

def map_application_with_hidden_fields(application, request):
    return {
        'uuid': str(application.uuid),
        'crews': application.crews,
        'event': application.event,
        'user': map_user_with_secret_fields(application.user, request),
        'last_processed_by': application.last_processed_by,
        'contents': application.contents,
        'created': int(application.created.timestamp()),
        'state': str(application.state),
        'answer': None if application.state == ApplicationState.created else application.answer,
        'hidden': application.hidden
    }