from decimal import ROUND_DOWN
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

from phoenixRest.models import Base

# We must make sure that classes that are used in relationships are loaded
from phoenixRest.models.tickets.ticket_type import TicketType
from phoenixRest.models.tickets.entrance import Entrance

import uuid

class Row(Base):
    __tablename__ = "row"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    
    row_number = Column(Integer, nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)

    is_horizontal = Column(Boolean, nullable=False)

    ticket_type_uuid = Column(UUID(as_uuid=True), ForeignKey("ticket_type.uuid"), nullable=True)
    ticket_type = relationship("TicketType")

    seatmap_uuid = Column(UUID(as_uuid=True), ForeignKey("seatmap.uuid"), nullable=False)
    seatmap = relationship("Seatmap", back_populates="rows")

    entrance_uuid = Column(UUID(as_uuid=True), ForeignKey("entrance.uuid"), nullable=True)
    entrance = relationship("Entrance")

    seats = relationship("Seat")

    def __init__(self, row_number: int, x: int, y: int, horizontal: bool, seatmap: Base, entrance: Entrance, ticket_type: TicketType):
        self.x = x
        self.y = y
        self.is_horizontal = horizontal
        self.seatmap = seatmap
        self.entrance = entrance
        self.ticket_type = ticket_type
        self.row_number = row_number

    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'x': self.x,
            'y': self.y,
            'is_horizontal': self.is_horizontal,
            'seatmap_uuid': self.seatmap_uuid,
            'entrance_uuid': self.entrance_uuid,
            'ticket_type_uuid': self.ticket_type_uuid,
            'row_number': self.row_number,
            'seats': sorted(self.seats, key=lambda seat: seat.number)
        }