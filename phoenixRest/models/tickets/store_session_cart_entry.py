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

from phoenixRest.models import db
from phoenixRest.models import Base

from phoenixRest.models.tickets.ticket_type import TicketType
from phoenixRest.models.tickets.store_session import StoreSession

from datetime import datetime, timedelta

class StoreSessionCartEntry(Base):
    __tablename__ = "store_session_cart_entry"

    store_session_uuid = Column(UUID(as_uuid=True), ForeignKey("store_session.uuid"), primary_key=True, nullable=False)
    store_session = relationship("StoreSession", back_populates="cart_entries")

    ticket_type_uuid = Column(UUID(as_uuid=True), ForeignKey("ticket_type.uuid"), primary_key=True, nullable=False)
    ticket_type = relationship("TicketType")

    amount = Column(Integer, nullable=False)


    def __init__(self, ticket_type: TicketType, amount: int):
        self.ticket_type = ticket_type
        self.amount = amount

    def __json__(self, request):
        return {
            'store_session_uuid': self.store_session_uuid,
            'ticket_type': self.ticket_type,
            'amount': self.amount
        }