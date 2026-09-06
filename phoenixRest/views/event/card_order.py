from pyramid.authorization import Allow
from pyramid.view import view_config

from phoenixRest.models.core.event import get_current_events
from phoenixRest.models.core.user import User
from phoenixRest.models.crew.card_order import CardOrder
from phoenixRest.roles import ADMIN, CHIEF
from phoenixRest.utils import validate


class EventCardOrderResource(object):
    def __acl__(self):
        return [
            (Allow, ADMIN(), 'create'),
            (Allow, CHIEF(self.event.event_brand_uuid), 'create')
        ]

    def __init__(self, request, event):
        self.request = request
        self.event = event


@view_config(context=EventCardOrderResource, request_method='POST', renderer='json', permission='create')
@validate(json_body={'user_uuid': str})
def create_card_order(context, request):
    active_events = list(map(lambda u: str(u), get_current_events(request.db)))
    if str(context.event.uuid) not in active_events:
        request.response.status = 400
        return {
            "error": "Event is not current - you can't create a card order for a non-current event"
        }

    subject_user = request.db.query(User) \
        .filter(User.uuid == request.json_body['user_uuid']) \
        .first()
    if subject_user is None:
        request.response.status = 400
        return {
            "error": "Subject user not found"
        }

    card_order = CardOrder(context.event, subject_user, request.user)
    request.db.add(card_order)
    request.db.flush()
    return card_order
