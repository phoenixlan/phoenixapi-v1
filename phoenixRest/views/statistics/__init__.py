from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from sqlalchemy import func, column, and_

from phoenixRest.models.core.event import Event, get_current_event
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.ticket_type import TicketType

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, CHIEF

from phoenixRest.views.seatmap.instance import SeatmapInstanceViews

import logging
log = logging.getLogger(__name__)

@resource(name='statistics')
class StatisticsViews(object):
    __acl__ = [
        (Allow, ADMIN, 'get_ticket_sales_stats'),
        (Allow, CHIEF, 'get_ticket_sales_stats'),
    ]
    def __init__(self, request):
        self.request = request

@view_config(name='ticket_sales', context=StatisticsViews, request_method='GET', renderer='json', permission='get_ticket_sales_stats')
def get_ticket_sales_stats(context, request):
    events = request.db.query(Event).all()

    include_free = False
    if "include_free" in request.GET:
        include_free = True

    # This COULD be a more complex sql query, but do we need it now? meh
    def generate_stats(event):
        date_list = func.generate_series(event.booking_time, event.start_time, '1 day').alias('days')

        day = column('days')

        possible_ticket_type_partial = request.db \
            .query(TicketType.uuid)
        if include_free:
            possible_ticket_type_partial = possible_ticket_type_partial.filter(and_(
                #TicketType.price != 0,
                TicketType.seatable == True
                ))
        else:
            possible_ticket_type_partial = possible_ticket_type_partial.filter(and_(
                TicketType.price != 0,
                TicketType.seatable == True
            ))
        possible_ticket_types = possible_ticket_type_partial.subquery()

        eligible_tickets = request.db \
            .query(Ticket) \
            .filter(and_(
                Ticket.event_uuid == event.uuid,
                Ticket.ticket_type_uuid.in_(possible_ticket_types)
            )) \
            .subquery().alias("eligible_tickets")

        result = request.db.query(func.row_number().over(order_by=day), day, func.count(eligible_tickets.c.ticket_id)).\
            select_from(date_list).\
            outerjoin(eligible_tickets, func.date_trunc('day', eligible_tickets.c.created) == func.date_trunc('day', day)).\
            group_by(day). \
            order_by(day.asc()). \
            all()
        
        return {
            "event": event,
            "days": [
                {
                    "idx": row[0],
                    "date": str(row[1].date()),
                    "count": row[2]
                } for row in result
            ]
        }

    results = [ generate_stats(event) for event in events]

    return results




