"""Membership personalia.
This table collects personalia that is used for membership info,
but that we don't want to store long-term if not in use."""
from sqlalchemy import (
    Column,
    DateTime,
    Date,
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
from sqlalchemy import or_

from phoenixRest.models import Base

from datetime import datetime, date

import enum
import uuid

# For passwordless test user
import os

import logging
log = logging.getLogger(__name__)

class MembershipPersonalia(Base):
    __tablename__ = "membership_personalia"
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user = relationship("User", back_populates="membership_personalia", uselist=False)

    address = Column(Text, nullable=False)
    postal_code = Column(Text, nullable=False)
    country_code = Column(Text, nullable=False, default="no")

    created = Column(DateTime, nullable=False, default=datetime.now)
    modified= Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def __init__(self, user: "User", address: str, postal_code: str, country_code: str):
        self.user = user
        self.address = address
        self.postal_code = postal_code

    def __json__(self, request):
        return {
            'user_uuid': str(self.user_uuid),
            'address': self.address,

            'postal_code': self.postal_code,
            'country_code': self.country_code,

            'created': self.created.timestamp(),
            'modified': self.created.timestamp(),
        }
    
