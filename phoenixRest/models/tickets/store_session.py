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

from phoenixRest.models import db, Base
from phoenixRest.models.core.user import User

from datetime import datetime, timedelta

import enum
import uuid

class StoreSession(Base):
    __tablename__ = "store_session"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    user = relationship("User")

    payment = relationship("Payment", back_populates="store_session")

    cart_entries = relationship("StoreSessionCartEntry", back_populates="store_session")

    created = Column(DateTime, nullable=False)
    expires = Column(DateTime, nullable=False)

    def __init__(self, user: User, expiry: int):
        self.user = user
        self.created = datetime.now()
        self.expires = self.created + timedelta(seconds=expiry)

    def get_total(self):
        sum = 0
        for entry in self.cart_entries:
            sum += entry.amount * entry.ticket_type.price
        
        return sum
    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'user_uuid': self.user_uuid,
            'entries': self.cart_entries,
            'total': self.get_total(),
            'created': int(self.created.timestamp()),
            'expires': int(self.expires.timestamp())
        }