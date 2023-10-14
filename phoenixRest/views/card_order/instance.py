from pyramid.authorization import Allow, Deny
from pyramid.httpexceptions import HTTPNotFound

from phoenixRest.roles import (
    CREW_CARD_PRINTER
)

from phoenixRest.utils import validateUuidAndQuery
from phoenixRest.models.crew.card_order import CardOrder, OrderStates

class CardOrderInstanceResource(object):
    def __acl__(self):
        acl = [
            # Roles with permission to generate a crew card based on an order
            (Allow, CREW_CARD_PRINTER, "generate"),
            
        ]
        return acl
    def __init__(self, request, uuid):
        self.request = request
        
        self.cardOrderInstance = validateUuidAndQuery(request, CardOrder, CardOrder.uuid, uuid)
        if self.cardOrderInstance == None:
            raise HTTPNotFound("card_order with specified uuid not found")

from pyramid.view import view_config

from datetime import datetime
from phoenixRest.features.crew_card import generate_badge
from phoenixRest.models.core.event import get_current_event

# Generates a crew card and updates the state of the order
@view_config(context=CardOrderInstanceResource, name='crew_card', request_method='PATCH', renderer='pillow', permission='generate')
def create_crew_card_from_order(context, request):
    context.CardOrderInstance.state = OrderStates.in_progress.value
    context.CardOrderInstance.last_updated = datetime.now()
    context.CardOrderInstance.updated_by_user = request.user
    
    return generate_badge(request, context.cardOrderInstance.subject_user, get_current_event(request))