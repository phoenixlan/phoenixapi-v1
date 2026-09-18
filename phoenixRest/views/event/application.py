from pyramid.authorization import Allow, Authenticated
from pyramid.view import view_config

from phoenixRest.models.core.event import get_current_events
from phoenixRest.models.crew.application import Application
from phoenixRest.models.crew.application_crew_mapping import ApplicationCrewMapping
from phoenixRest.models.crew.crew import Crew
from phoenixRest.utils import validate


class EventApplicationResource(object):
    __acl__ = [
        (Allow, Authenticated, 'create')
    ]

    def __init__(self, request, event):
        self.request = request
        self.event = event


@view_config(context=EventApplicationResource, request_method='PUT', renderer='json', permission='create')
@validate(json_body={'crews': list, 'contents': str})
def create_application(context, request):
    if request.user.avatar is None:
        request.response.status = 400
        return {
            "error": "You must upload an avatar before you can apply for crew"
        }

    if len(request.json_body['crews']) > 3:
        request.response.status = 400
        return {
            "error": "Too many crews"
        }
    elif len(request.json_body['crews']) == 0:
        request.response.status = 400
        return {
            "error": "You need to apply to at least one crew"
        }

    if len(set(request.json_body['crews'])) != len(request.json_body['crews']):
        request.response.status = 400
        return {
            "error": "Duplicates are not allowed"
        }

    crew_list = list(map(
        lambda crew: request.db.query(Crew).filter(Crew.uuid == crew).first(),
        request.json_body['crews']
    ))

    if None in crew_list:
        request.response.status = 400
        return {
            "error": "Crew not found"
        }

    for crew in crew_list:
        if crew.event_brand_uuid != context.event.event_brand_uuid:
            request.response.status = 400
            return {
                "error": "Crew belongs to a different event brand"
            }
        if not crew.is_applyable:
            request.response.status = 400
            return {
                "error": "You cannot apply to %s" % crew.name
            }

    active_events = list(map(lambda u: str(u), get_current_events(request.db)))
    if str(context.event.uuid) not in active_events:
        request.response.status = 400
        return {
            "error": "Event is not current - you can't create an application for a non-current event"
        }

    application = Application(
        user=request.user,
        event=context.event,
        crews=list(map(lambda crew: ApplicationCrewMapping(crew), crew_list)),
        contents=request.json_body['contents']
    )
    request.db.add(application)
    request.db.flush()

    request.service_manager.get_service('email').send_mail(
        request.user.email,
        "Mottatt søknad",
        "application_received.jinja2",
        {
            "mail": request.registry.settings["api.contact"],
            "name": request.registry.settings["api.name"],
            "crew_list": crew_list
        }
    )

    return application
