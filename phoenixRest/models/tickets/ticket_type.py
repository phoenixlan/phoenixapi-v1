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

from phoenixRest.models import Base

import uuid

class TicketType(Base):
    __tablename__ = "ticket_type"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    name = Column(Text, nullable=False)

    price = Column(Integer, nullable=False)

    refundable = Column(Boolean, default=True, nullable=False)

    seatable = Column(Boolean, nullable=False, default=True)

    requires_membership = Column(Boolean, server_default="false", nullable=False)
    grants_membership = Column(Boolean, server_default="true", nullable=False)
    
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
            'description': self.description,
            'requires_membership': self.requires_membership,
            'grants_membership': self.grants_membership
        }
