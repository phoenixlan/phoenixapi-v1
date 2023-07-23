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
    Identity
)
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship

from phoenixRest.models import Base

from datetime import datetime, timedelta

import uuid

class TicketVoucher(Base):
    __tablename__ = "ticket_voucher"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    
    source_user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    source_user = relationship("User", foreign_keys=[source_user_uuid])

    recipient_user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    recipient_user = relationship("User", foreign_keys=[recipient_user_uuid])

    ticket_type_uuid = Column(UUID(as_uuid=True), ForeignKey("ticket_type.uuid"), nullable=False)
    ticket_type = relationship("TicketType")

    # The ticket once the ticket voucher is generated
    ticket_id = Column(Integer, ForeignKey("ticket.ticket_id"), nullable=True)
    ticket = relationship("Ticket")

    # INCLUDING
    last_use_event_uuid = Column(UUID(as_uuid=True), ForeignKey("event.uuid"), nullable=False)
    last_use_event = relationship("Event")

    used = Column(DateTime, nullable=True)

    created = Column(DateTime, nullable=False)

    def __init__(self, source_user, recipient_user, ticket_type, last_use_event):
        self.source_user = source_user
        self.recipient_user = recipient_user

        self.ticket_type = ticket_type

        self.last_use_event = last_use_event

        self.created = datetime.now()

    def __json__(self, request):
        return {
            'uuid': self.uuid,
            'recipient_user': self.recipient_user,
            'ticket_type': self.ticket_type,
            'last_use_event': self.last_use_event,

            'ticket': self.ticket,

            'created': int(self.created.timestamp()),
            'used': int(self.used.timestamp()) if self.used is not None else None,
            'expired': self.is_expired(request),
        }

    def is_expired(self, request):
        return self.last_use_event.end_time < datetime.now()