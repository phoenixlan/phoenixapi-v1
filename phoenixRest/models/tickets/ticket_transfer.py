
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

from phoenixRest.models import db
from phoenixRest.models import Base

from phoenixRest.models.core.user import User

from phoenixRest.models.tickets.payment import Payment
from phoenixRest.models.tickets.ticket_type import TicketType

from datetime import datetime, timedelta

import string
import uuid

class TicketTransfer(Base):
    __tablename__ = "ticket_transfer"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    
    from_user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    from_user = relationship("User", foreign_keys=[from_user_uuid])

    to_user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    to_user = relationship("User", foreign_keys=[to_user_uuid])

    ticket_uuid = Column(Integer, ForeignKey("ticket.ticket_id"), nullable=False)
    ticket = relationship("Ticket")

    reverted = Column(Boolean, nullable=False, server_default="false")

    created = Column(DateTime, nullable=False)

    def __init__(self, from_user, to_user, ticket):
        self.from_user = from_user
        self.to_user = to_user
        self.ticket = ticket

        self.created = datetime.now()

    def __json__(self, request):
        expiry_offset = int(request.registry.settings['ticket.transfer.expiry'])
        expiry_time = self.created + timedelta(seconds=expiry_offset)

        return {
            'uuid': self.uuid,
            'from_user': self.from_user,
            'to_user': self.to_user,
            'ticket': self.ticket,

            'created': int(self.created.timestamp()),
            'expired': self.is_expired(request),
            'expires': int(expiry_time.timestamp()),
            'reverted': self.reverted
        }

    def is_expired(self, request):
        expiry_offset = int(request.registry.settings['ticket.transfer.expiry'])
        expiry_time = self.created + timedelta(seconds=expiry_offset)
        return datetime.now() > expiry_time