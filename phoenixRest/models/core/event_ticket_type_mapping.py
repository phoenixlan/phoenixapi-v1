"""Describes the relationship between a ticket type and an event"""
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Integer,
    Text,
    ARRAY
)
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship

from phoenixRest.models import Base
from phoenixRest.utils import randomCode

from datetime import datetime

import logging
log = logging.getLogger(__name__)

import uuid

class EventTicketTypeMapping(Base):
    __tablename__ = "event_ticket_type_mapping"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    event_uuid = Column(UUID(as_uuid=True), ForeignKey("event.uuid"), nullable=False)
    event= relationship("Event", back_populates="ticket_types", uselist=False)

    ticket_type_uuid = Column(UUID(as_uuid=True), ForeignKey("ticket_type.uuid"), nullable=False)
    ticket_type = relationship("TicketType", uselist=False)

    sales_cap= Column(Integer, nullable=True)
    sales_cap_groups = Column(ARRAY(Text), nullable=False)

    # If set, this mapping is not shown to people unless they have "activated" the mapping by entering the code
    access_code = Column(Text)

    created = Column(DateTime, nullable=False, default=datetime.now)
    modified= Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint('event_uuid', 'ticket_type_uuid', name='_event_tickettype_uic'),
    )

    def __init__(self, event, ticket_type, sales_cap_groups, generate_code: bool, sales_cap):
        self.event = event
        self.ticket_type = ticket_type
        self.sales_cap = sales_cap
        self.sales_cap_groups = sales_cap_groups

        if generate_code:
            self.access_code = EventTicketTypeMapping.get_access_code()

    @staticmethod
    def get_access_code() -> str:
        """Generates a new access code. Used both when creating and when rotating access codes"""
        return randomCode(10)

    def __json__(self, request):
        return {
            'uuid': self.uuid,

            'event_uuid': self.event_uuid,
            'ticket_type': self.ticket_type,

            'sales_cap': self.sales_cap,
            'sales_cap_groups': self.sales_cap_groups,

            'access_code': self.access_code,

            'created': int(self.created.timestamp()),
            'modified': int(self.modified.timestamp())
        }
