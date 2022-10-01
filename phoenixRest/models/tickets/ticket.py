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

from phoenixRest.mappers.seat import map_seat_for_ticket

from datetime import datetime, timedelta

import string
import uuid

class Ticket(Base):
    __tablename__ = "ticket"
    ticket_id = Column(Integer, Identity(start=1, cycle=False), primary_key = True, nullable=False)
    
    buyer_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    buyer = relationship("User", foreign_keys=[buyer_uuid], back_populates="purchased_tickets")

    owner_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    owner = relationship("User", foreign_keys=[owner_uuid], back_populates="owned_tickets")

    seater_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    seater = relationship("User", foreign_keys=[seater_uuid], back_populates="seatable_tickets")

    payment_uuid = Column(UUID(as_uuid=True), ForeignKey("payment.uuid"), nullable=True)
    payment = relationship("Payment")

    ticket_type_uuid = Column(UUID(as_uuid=True), ForeignKey("ticket_type.uuid"), nullable=False)
    ticket_type = relationship("TicketType")

    event_uuid = Column(UUID(as_uuid=True), ForeignKey("event.uuid"), nullable=False)
    event = relationship("Event")

    seat_uuid = Column(UUID(as_uuid=True), ForeignKey("seat.uuid"), nullable=True)
    seat = relationship("Seat", back_populates="ticket")

    created = Column(DateTime, nullable=False)

    checked_in = Column(DateTime, nullable=True)

    def __init__(self, buyer: User, payment: Payment, ticket_type: TicketType, event):
        self.buyer = buyer
        self.owner = buyer
        self.seater = buyer
        self.payment = payment
        self.ticket_type = ticket_type
        self.event = event

        self.created = datetime.now()

    def __json__(self, request):
        return {
            'ticket_id': self.ticket_id,
            'buyer': self.buyer,
            'owner': self.owner,
            'seater': self.seater,

            'payment_uuid': self.payment_uuid,
            'ticket_type': self.ticket_type,

            'event_uuid': self.event_uuid,
            'checked_in': int(self.checked_in.timestamp()) if self.checked_in is not None else None,

            'seat': map_seat_for_ticket(self.seat) if self.seat is not None else None,

            'created': int(self.created.timestamp())
        }