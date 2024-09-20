from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import (
    HTTPForbidden,
)
from pyramid.authorization import Authenticated, Everyone, Deny, Allow

from sqlalchemy import func, column, and_, extract

from phoenixRest.models.core.event import Event, get_current_event
from phoenixRest.models.core.user import User
from phoenixRest.models.crew.position_mapping import PositionMapping
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.ticket_type import TicketType

from phoenixRest.utils import validate
from phoenixRest.resource import resource

from phoenixRest.roles import ADMIN, CHIEF

from phoenixRest.views.seatmap.instance import SeatmapInstanceViews

import logging
log = logging.getLogger(__name__)

from datetime import date

@resource(name='statistics')
class StatisticsViews(object):
    __acl__ = [
        (Allow, ADMIN, 'get_ticket_sales_stats'),
        (Allow, CHIEF, 'get_ticket_sales_stats'),

        (Allow, ADMIN, 'get_participant_history_stats'),
        (Allow, CHIEF, 'get_participant_history_stats'),

        (Allow, ADMIN, 'get_age_distribution_stats'),
        (Allow, CHIEF, 'get_age_distribution_stats'),
    ]
    def __init__(self, request):
        self.request = request

@view_config(name='age_distribution', context=StatisticsViews, request_method='GET', renderer='json', permission='get_age_distribution_stats')
def get_age_distribution(context, request):
    events = request.db.query(Event).all()

    def generate_stats(event):
        age_distribution = []
        crew_age_distribution = []

        participants = request.db.query(User.uuid, func.extract('year', func.age(Event.start_time, User.birthdate)).label("age") ) \
            .join(Ticket, Ticket.owner_uuid == User.uuid, isouter=True) \
            .join(Event, Event.uuid == Ticket.event_uuid) \
            .filter(
                Ticket.event == event
            ) \
            .distinct(User.uuid).subquery()

        log.info(participants)
        age_counts = request.db.query(participants.c.age, func.count(participants.c.age).label("age_count")).group_by(participants.c.age).all()

        crews = request.db.query(User.uuid, func.extract('year', func.age(Event.start_time, User.birthdate)).label("age") ) \
            .join(PositionMapping, PositionMapping.user_uuid == User.uuid) \
            .join(Event, Event.uuid == PositionMapping.event_uuid) \
            .filter(
                PositionMapping.event == event
            ).distinct(User.uuid).subquery()
        crew_age_counts = request.db.query(crews.c.age, func.count(crews.c.age).label("age_count")).group_by(crews.c.age).all()

        for part in age_counts:
            print(part)
            age, count = part
            age = int(age)

            if len(age_distribution) <= age:
                age_distribution = age_distribution + ( [0] * (age- len(age_distribution) + 1) )
            age_distribution[age] += count

        for part in crew_age_counts:
            print(part)
            age, count = part
            age = int(age)

            if len(crew_age_distribution) <= age:
                crew_age_distribution = crew_age_distribution + ( [0] * (age- len(crew_age_distribution) + 1) )
            crew_age_distribution[age] += count

        log.info(f"{age_counts}")

        return {
            "event": event,
            "age_distribution": age_distribution,
            "crew_age_distribution":crew_age_distribution 
        }

    return [ generate_stats(event) for event in events]

@view_config(name='participant_history', context=StatisticsViews, request_method='GET', renderer='json', permission='get_participant_history_stats')
def get_participant_history(context, request):
    events = request.db.query(Event).all()

    def generate_stats(event):
        crew_counts = []

        # All our participants
        eligible_users = request.db.query(User.uuid).join(Ticket, Ticket.owner_uuid == User.uuid).filter(
            Ticket.event == event
        ).distinct(User.uuid).subquery()

        # All tickets they have owned from other events
        visited_events = request.db.query(Ticket) \
            .join(Event, Event.uuid == Ticket.event_uuid) \
            .filter(and_(
                Ticket.event != event,
                Ticket.owner_uuid.in_(eligible_users),
                Event.start_time < event.start_time
        )).distinct(Event.uuid, Ticket.owner_uuid).subquery()

        user_participations_statement = request.db.query(eligible_users, func.count(visited_events.c.owner_uuid)) \
            .join(visited_events, visited_events.c.owner_uuid == eligible_users.c.uuid, isouter=True) \
            .group_by(eligible_users.c.uuid)
        user_participations = user_participations_statement.all()

        # Now determine participation for crew
        eligible_crew_members = request.db.query(User.uuid).join(PositionMapping, PositionMapping.user_uuid == User.uuid).filter(
            PositionMapping.event == event
        ).distinct(User.uuid).subquery()

        crew_participated_events = request.db.query(PositionMapping) \
            .join(Event, Event.uuid == PositionMapping.event_uuid) \
            .filter(and_(
                PositionMapping.event != event,
                PositionMapping.user_uuid.in_(eligible_crew_members),
                Event.start_time < event.start_time
        )).distinct(Event.uuid, PositionMapping.user_uuid).subquery()

        crew_participations_statement = request.db.query(eligible_crew_members, func.count(crew_participated_events.c.user_uuid)) \
            .join(crew_participated_events, crew_participated_events.c.user_uuid == eligible_crew_members.c.uuid, isouter=True) \
            .group_by(eligible_crew_members.c.uuid)
        crew_participations = crew_participations_statement.all()

        counts = []

        for part in user_participations:
            print(part)
            _, count = part
            if len(counts) <= count:
                counts = counts + ( [0] * (count - len(counts) + 1) )
            counts[count] += 1

        for part in crew_participations:
            print(part)
            _, count = part
            if len(crew_counts) <= count:
                crew_counts = crew_counts + ( [0] * (count - len(crew_counts) + 1) )
            crew_counts[count] += 1

        return {
            "event": event,
            "counts": counts,
            "crew_counts": crew_counts
        }

    return [ generate_stats(event) for event in events]

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




