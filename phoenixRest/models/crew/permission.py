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

from phoenixRest.models.core.user import User
from phoenixRest.models.core.event import Event
from phoenixRest.models.crew.position import Position

from datetime import datetime, timedelta

from typing import Union

import secrets
import string
import uuid

class Permission(Base):
    __tablename__ = "permission_binding"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    position_uuid = Column(UUID(as_uuid=True), ForeignKey("position.uuid"), nullable=False)
    position = relationship("Position", back_populates="permissions")

    event_uuid = Column(UUID(as_uuid=True), ForeignKey("event.uuid"), nullable=True)
    event = relationship("Event")

    permission = Column(Text, nullable=False)

    def __init__(self, position: Position, permission: str, event: Union[None, Event]):
        self.position = position
        self.permission = permission
        self.event = event

    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'event_uuid': str(self.event_uuid) if self.event_uuid else None,
            'permission': self.permission
        }