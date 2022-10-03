
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

from datetime import datetime, timedelta

import logging
log = logging.getLogger(__name__)

import secrets
import string
import uuid

class PositionMapping(Base):
    __tablename__ = "user_positions"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    position_uuid = Column(UUID(as_uuid=True), ForeignKey("position.uuid"), nullable=False, primary_key=True)
    position = relationship("Position", back_populates="position_mappings", uselist=False)

    user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False, primary_key=True)
    user = relationship("User", back_populates="position_mappings", uselist=False)

    event_uuid = Column(UUID(as_uuid=True), ForeignKey("event.uuid"), nullable=True)
    event = relationship("Event")

    created = Column(DateTime, nullable=False)

    def __init__(self, user, position, event=None):
        self.user = user
        self.position = position
        self.event = event
        self.created = datetime.now()

        return {
            'position_uuid': str(self.position_uuid),
            'user_uuid': str(self.user_uuid),
            'event_uuid': str(self.event_uuid),
            'created': int(self.created.timestamp())
        }
