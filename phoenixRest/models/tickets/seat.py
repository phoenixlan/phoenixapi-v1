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

from phoenixRest.models.tickets.ticket import Ticket

from datetime import datetime, timedelta

import string
import uuid

class Seat(Base):
    __tablename__ = "seat"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    
    number = Column(Integer, nullable=False)

    is_reserved = Column(Boolean, default=False)

    row_uuid = Column(UUID(as_uuid=True), ForeignKey("row.uuid"), nullable=False)
    row = relationship("Row", back_populates="seats")

    ticket = relationship("Ticket", back_populates="seat")

    def __init__(self, number: int, row):
        self.number = number
        self.row = row

    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'number': self.number,
            'is_reserved': self.is_reserved,
            'row_uuid': self.row_uuid
        }