from pyramid.authorization import Allow
from phoenixRest.roles import CHIEF, CREW_CARD_PRINTER, ADMIN

from pyramid.view import view_config
from phoenixRest.resource import resource
from phoenixRest.utils import validate

from phoenixRest.models.core.event import Event, get_current_events
from phoenixRest.models.core.user import User
from phoenixRest.models.crew.card_order import CardOrder
from phoenixRest.views.card_order.instance import CardOrderInstanceResource

@resource(name="card_order")
class CardOrderResource(object):
    __acl__ = [
        # Roles with permission to create a new card order
         (Allow, CHIEF, "create"),
         (Allow, ADMIN, "create")
    ]   
         
    def __init__(self, request):
        self.request = request  
        
    def __getitem__(self, key):
        node = CardOrderInstanceResource(self.request, key)
        node.__parent__ = self
        node.__name__ = key
        return node

# Creates a new card order
@view_config(name="", context=CardOrderResource, request_method="POST", renderer="json", permission="create")
@validate(json_body={"user_uuid": str, "event_uuid": str})
def create_card_order(context, request):
    event = request.db.query(Event).filter(Event.uuid == request.json_body['event_uuid']).first()
    if not event:
        request.response.status = 400
        return {
            "error": "Event not found"
        }

    active_events = list(map(lambda u: str(u), get_current_events(request.db)))
    if str(event.uuid) not in active_events:
        request.response.status = 400
        return {
            "error": "Event is not current - you can't create an application for a non-current event"
        }
    
    subject_user_uuid = request.json_body["user_uuid"]
    subject_user = request.db.query(User).filter(User.uuid == subject_user_uuid).first()
    if subject_user is None:
        request.response.status = 400
        return {
            "error": "Subject user not found"
        }
    
    creator_user = request.user
    
    card_order = CardOrder(event, subject_user, creator_user)
    request.db.add(card_order)
    request.db.flush()
    
    return card_order
