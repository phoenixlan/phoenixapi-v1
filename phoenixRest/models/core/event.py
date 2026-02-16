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
    Table
)
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship
from sqlalchemy import and_

from phoenixRest.models import Base

from phoenixRest.models.core.user import User
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.ticket_type import TicketType

# We must make sure that classes that are used in relationships are loaded
from phoenixRest.models.tickets.seatmap import Seatmap

from datetime import datetime, timedelta

from typing import Optional

import logging
log = logging.getLogger(__name__)

import secrets
import string
import uuid

EventTicketTypeAssociation = Table('event_ticket_type_static_assoc', Base.metadata, 
    Column('event_uuid', UUID(as_uuid=True), ForeignKey('event.uuid')),
    Column('ticket_type_uuid', UUID(as_uuid=True), ForeignKey('ticket_type.uuid'))
)
class Event(Base):
    __tablename__ = "event"

    name = Column(Text, nullable=False)
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    # Start and end time of event
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    booking_time = Column(DateTime, nullable=False)
    
    # Delta in seconds from booking time
    priority_seating_time_delta = Column(Integer, nullable=False)
    seating_time_delta = Column(Integer, nullable=False)

    max_participants = Column(Integer, nullable=False)
    participant_age_limit_inclusive = Column(Integer, nullable=False, server_default="-1")
    crew_age_limit_inclusive = Column(Integer, nullable=False, server_default="-1")

    theme = Column(Text)

    location_uuid = Column(UUID(as_uuid=True), ForeignKey("location.uuid"), nullable=True)
    location = relationship("Location")

    seatmap_uuid = Column(UUID(as_uuid=True), ForeignKey("seatmap.uuid"), nullable=True)
    seatmap = relationship("Seatmap")

    static_ticket_types = relationship("TicketType", secondary=EventTicketTypeAssociation)

    cancellation_reason = Column(Text)

    def __init__(self, name: str, start_time: DateTime, end_time: DateTime, booking_time: DateTime, priority_seating_time_delta: int, seating_time_delta: int, 
                 max_participants: int, participant_age_limit_inclusive: int, crew_age_limit_inclusive: int, theme: Optional[str], location_uuid: Optional[str], 
                 seatmap_uuid: Optional[str]):
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.booking_time = booking_time
        self.priority_seating_time_delta = priority_seating_time_delta
        self.seating_time_delta = seating_time_delta
        self.max_participants = max_participants
        self.participant_age_limit_inclusive = participant_age_limit_inclusive
        self.crew_age_limit_inclusive = crew_age_limit_inclusive
        self.theme = theme
        self.location_uuid = location_uuid
        self.seatmap_uuid = seatmap_uuid


    def __json__(self, request):
        return {
            'name': str(self.name),
            'uuid': str(self.uuid),
            'start_time': int(self.start_time.timestamp()),
            'end_time': int(self.end_time.timestamp()),
            'booking_time': int(self.booking_time.timestamp()),
            'priority_seating_time_delta': self.priority_seating_time_delta,
            'seating_time_delta': self.seating_time_delta,
            'max_participants': self.max_participants,
            'participant_age_limit_inclusive': self.participant_age_limit_inclusive,
            'crew_age_limit_inclusive': self.crew_age_limit_inclusive,
            'theme': self.theme,
            'location_uuid': self.location_uuid,
            'seatmap_uuid': self.seatmap_uuid,
            'cancellation_reason': self.cancellation_reason
        }
    
    """
    Returns a numer prepresenting the total number of tickets left for the event
    """
    def get_total_ticket_availability(self, request):
        return self.max_participants - request.db.query(Ticket) \
            .join(TicketType, Ticket.ticket_type_uuid == TicketType.uuid) \
            .filter(and_(
                TicketType.seatable == True,
                Ticket.event_uuid == self.uuid
            )) \
            .count()

    def foo(self):
        log.info("foo bar!")

def get_current_event(request):
    firstEvent = request.db.query(Event).filter(Event.end_time > datetime.now()).order_by(Event.start_time.asc()).first()
    if firstEvent is None:
        logging.warning("There are no new events")
        return None
    else:
        # TODO we want to return ticket types some time? Maybe?
        return firstEvent

def get_most_recent_event(request):
    mostRecentEvent = request.db.query(Event).filter(Event.end_time < datetime.now()).order_by(Event.start_time.asc()).first()
    if mostRecentEvent is None:
        logging.warning("There is no most recent event")
        return None
    else:
        return mostRecentEvent