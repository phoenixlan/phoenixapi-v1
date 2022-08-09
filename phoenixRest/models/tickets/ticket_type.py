"""Payment object"""
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    Text,
    Boolean,
    Enum,
    Table
)
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship

from phoenixRest.models import db
from phoenixRest.models import Base

from phoenixRest.models.core.user import User

from datetime import datetime, timedelta

import secrets
import string
import uuid

class TicketType(Base):
    __tablename__ = "ticket_type"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    name = Column(Text, nullable=False)

    price = Column(Integer, nullable=False)

    refundable = Column(Boolean, default=True, nullable=False)

    seatable = Column(Boolean, nullable=False, default=True)
    
    description = Column(Text)
    

    def __init__(self, name: str, price: int, description: str, refundable: bool, seatable: bool):
        self.name = name
        self.price = price
        self.description = description 
        self.refundable = refundable
        self.seatable = seatable


    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'name': self.name,
            'price': self.price,
            'refundable': self.refundable,
            'seatable': self.seatable,
            'description': self.description
        }
