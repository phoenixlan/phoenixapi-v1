"""Payment object"""
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

from phoenixRest.models import db
from phoenixRest.models import Base

from phoenixRest.models.core.user import User
from phoenixRest.models.tickets.ticket import Ticket
from phoenixRest.models.tickets.ticket_type import TicketType

# We must make sure that classes that are used in relationships are loaded
from phoenixRest.models.tickets.seatmap import Seatmap

from datetime import datetime, timedelta

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
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    booking_time = Column(DateTime, nullable=False)
    
    # Delta in seconds from booking time
    priority_seating_time_delta = Column(Integer, nullable=False)
    seating_time_delta = Column(Integer, nullable=False)

    # Start and end time of event
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    name = Column(Text, nullable=False)

    theme = Column(Text)
    max_participants = Column(Integer, nullable=False)

    age_limit_inclusive = Column(Integer, nullable=False, server_default="-1")

    location_uuid = Column(UUID(as_uuid=True), ForeignKey("location.uuid"), nullable=True)
    location = relationship("Location")

    seatmap_uuid = Column(UUID(as_uuid=True), ForeignKey("seatmap.uuid"), nullable=True)
    seatmap = relationship("Seatmap")

    static_ticket_types = relationship("TicketType", secondary=EventTicketTypeAssociation)

    cancellation_reason = Column(Text)

    def __init__(self, name: str, start_time: DateTime, end_time: DateTime, max_participants: int):
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.booking_time = start_time - timedelta(days=31)
        self.priority_seating_time_delta = 60*30
        self.seating_time_delta = 60*60
        self.max_participants = max_participants


    def __json__(self, request):
        return {
            'name': str(self.name),
            'uuid': str(self.uuid),
            'age_limit_inclusive': self.age_limit_inclusive,
            'booking_time': int(self.booking_time.timestamp()),
            'priority_seating_time_delta': self.priority_seating_time_delta,
            'seating_time_delta': self.seating_time_delta,
            'start_time': int(self.start_time.timestamp()),
            'end_time': int(self.end_time.timestamp()),
            'theme': self.theme,
            'max_participants': self.max_participants,
            'cancellation_reason': self.cancellation_reason,
            'seatmap_uuid': self.seatmap_uuid,
            'location': self.location
        }
    
    """
    Returns a numer prepresenting the total number of tickets left for the event
    """
    def get_total_ticket_availability(self):
        return self.max_participants - db.query(Ticket) \
            .join(TicketType, Ticket.ticket_type_uuid == TicketType.uuid) \
            .filter(and_(
                TicketType.seatable == True,
                Ticket.event_uuid == self.uuid
            )) \
            .count()

def get_current_event():
    firstEvent = db.query(Event).filter(Event.end_time > datetime.now()).order_by(Event.start_time.asc()).first()
    if firstEvent is None:
        logging.warning("There are no new events")
        return None
    else:
        # TODO we want to return ticket types some time? Maybe?
        return firstEvent

