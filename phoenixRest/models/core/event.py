from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    Text,
    Integer,
    Boolean,
    Enum,
    Table,
    func,
    JSON
)
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship
from sqlalchemy import and_

from phoenixRest.models import Base

from phoenixRest.models.core.event_brand import EventBrand
from phoenixRest.models.core.event_ticket_type_mapping import EventTicketTypeMapping
from phoenixRest.models.core.user import User
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.ticket_type import TicketType
from phoenixRest.models.tickets.store_session import StoreSession
from phoenixRest.models.tickets.store_session_cart_entry import StoreSessionCartEntry

# We must make sure that classes that are used in relationships are loaded
from phoenixRest.models.tickets.seatmap import Seatmap

from datetime import datetime, timedelta

from typing import Optional

import logging
log = logging.getLogger(__name__)

import secrets
import string
import uuid

class Event(Base):
    __tablename__ = "event"

    name = Column(Text, nullable=False)
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    event_brand_uuid = Column(UUID(as_uuid=True), ForeignKey("event_brand.uuid"), nullable=False)
    event_brand = relationship("EventBrand", back_populates="events")

    # Start and end time of event
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    booking_time = Column(DateTime, nullable=False)
    
    # Delta in seconds from booking time
    priority_seating_time_delta = Column(Integer, nullable=False)
    seating_time_delta = Column(Integer, nullable=False)

    # A dict where the key is sales cap group and the value is an int describing what the max number of ticket that can be sold is
    ticket_sales_caps = Column(JSON, nullable=False, server_default='{}')

    participant_age_limit_inclusive = Column(Integer, nullable=False, server_default="-1")
    crew_age_limit_inclusive = Column(Integer, nullable=False, server_default="-1")

    theme = Column(Text)

    location_uuid = Column(UUID(as_uuid=True), ForeignKey("location.uuid"), nullable=True)
    location = relationship("Location")

    seatmap_uuid = Column(UUID(as_uuid=True), ForeignKey("seatmap.uuid"), nullable=True)
    seatmap = relationship("Seatmap")

    cancellation_reason = Column(Text)

    ticket_types = relationship("EventTicketTypeMapping", back_populates="event", order_by="EventTicketTypeMapping.created")

    def __init__(self, name: str, start_time: DateTime, end_time: DateTime, booking_time: DateTime, priority_seating_time_delta: int, seating_time_delta: int,
                 ticket_sales_caps: dict, participant_age_limit_inclusive: int, crew_age_limit_inclusive: int, theme: Optional[str], location_uuid: Optional[str],
                 seatmap_uuid: Optional[str], event_brand):
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.booking_time = booking_time
        self.priority_seating_time_delta = priority_seating_time_delta
        self.seating_time_delta = seating_time_delta
        self.ticket_sales_caps = ticket_sales_caps

        self.event_brand = event_brand
        
        self.participant_age_limit_inclusive = participant_age_limit_inclusive
        self.crew_age_limit_inclusive = crew_age_limit_inclusive
        self.theme = theme
        self.location_uuid = location_uuid
        self.seatmap_uuid = seatmap_uuid

    def __json__(self, request):
        return {
            'name': str(self.name),
            'uuid': str(self.uuid),
            'event_brand_uuid': str(self.event_brand_uuid),
            'participant_age_limit_inclusive': self.participant_age_limit_inclusive,
            'crew_age_limit_inclusive': self.crew_age_limit_inclusive,
            'start_time': int(self.start_time.timestamp()),
            'end_time': int(self.end_time.timestamp()),
            'booking_time': int(self.booking_time.timestamp()),
            'priority_seating_time_delta': self.priority_seating_time_delta,
            'seating_time_delta': self.seating_time_delta,
            'ticket_sales_caps': self.ticket_sales_caps,
            'participant_age_limit_inclusive': self.participant_age_limit_inclusive,
            'crew_age_limit_inclusive': self.crew_age_limit_inclusive,
            'theme': self.theme,
            'location_uuid': self.location_uuid,
            'seatmap_uuid': self.seatmap_uuid,
            'cancellation_reason': self.cancellation_reason
        }

    def get_sales_by_ticket_type(self, db):
        """Returns a dict where the key is a ticket type UUID and the value is the number of tickets sold"""
        # No. of sold tickets per ticket type
        sold = dict(db.query(Ticket.ticket_type_uuid, func.count(Ticket.ticket_id)) \
            .filter(Ticket.event_uuid == self.uuid) \
            .group_by(Ticket.ticket_type_uuid) \
            .all())

        # No of reserved tickets per ticket type
        reserved = db.query(StoreSessionCartEntry.ticket_type_uuid, func.sum(StoreSessionCartEntry.amount)) \
            .join(StoreSession, StoreSession.uuid == StoreSessionCartEntry.store_session_uuid) \
            .filter(and_(
                StoreSession.event_uuid == self.uuid,
                StoreSession.expires > datetime.now()
            )) \
            .group_by(StoreSessionCartEntry.ticket_type_uuid) \
            .all()

        # Add reserved numbers to the sold counts
        for ticket_type_uuid, amount in reserved:
            sold[ticket_type_uuid] = sold.get(ticket_type_uuid, 0) + amount

        return sold
    
    def get_ticket_group_availability(self, db, ticket_type_sales):
        """
        Returns a dict with the number of tickets left for each sales cap group configured in ticket_sales_caps.
        Every ticket type counts towards the groups it belongs to.
        Tickets reserved by store sessions that haven't expired yet count as sold
        """


        availability = dict()
        for group, cap in self.ticket_sales_caps.items():
            group_sold = sum(
                ticket_type_sales.get(mapping.ticket_type_uuid, 0) for mapping in self.ticket_types
                if group in mapping.sales_cap_groups
            )
            availability[group] = max(cap - group_sold, 0)
        return availability

    def get_ticket_type_availability(self, db, ticket_type_sales: dict, group_availability: dict):
        """
        Returns the number of tickets left for each ticket type mapped to the event, given the group availability
        from get_ticket_group_availability. A ticket type is limited by its own sales cap and by every group it
        belongs to. remaining is None if nothing limits the ticket type
        """
        availability = list()
        for mapping in self.ticket_types:
            limits = [ group_availability[group] for group in mapping.sales_cap_groups if group in group_availability ]
            if mapping.sales_cap is not None:
                limits.append(max(mapping.sales_cap - ticket_type_sales.get(mapping.ticket_type_uuid, 0), 0))

            availability.append({
                'ticket_type_mapping_uuid': mapping.uuid,
                'ticket_type': mapping.ticket_type,
                'groups': mapping.sales_cap_groups,
                'remaining': min(limits) if len(limits) > 0 else None
            })
        return availability

def validate_ticket_sales_caps(ticket_sales_caps) -> Optional[str]:
    """Returns an error message if ticket_sales_caps is not a dict of group name to a non-negative number of tickets"""
    if type(ticket_sales_caps) != dict:
        return "Invalid type of ticket_sales_caps (not object)"
    for group, cap in ticket_sales_caps.items():
        if len(group.strip()) == 0:
            return "ticket_sales_caps cannot contain an empty group name"
        if type(cap) != int:
            return "Invalid type of ticket_sales_caps value for group %s (not integer)" % group
        if cap < 0:
            return "ticket_sales_caps value for group %s cannot be negative" % group
    return None

def get_current_events(db):
    """Returns the uuid of all active events, one per brand.
    We use uuid as it is more useful"""
    ranked_sub = db.query(
        Event.uuid.label("uuid"), 
        func.row_number().over(partition_by=Event.event_brand_uuid, order_by=Event.end_time.asc()).label("rank")
    ).filter(Event.end_time > datetime.now()).subquery()

    current_events = list(map(lambda row: row[0], db.query(ranked_sub.c.uuid).filter(ranked_sub.c.rank == 1).all()))
    log.info(f"Current events: {current_events}")

    return current_events


def get_current_event(db, brand: "Brand"):
    """Returns the current event for a given brand"""
    firstEvent = db.query(Event).filter(Event.end_time > datetime.now(), Event.event_brand_uuid == brand.uuid).order_by(Event.start_time.asc()).first()
    if firstEvent is None:
        logging.warning(f"There are no new events for brand {brand.uuid}")
        return None
    else:
        # TODO we want to return ticket types some time? Maybe?
        return firstEvent
