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

from phoenixRest.models.core.event import Event

from datetime import datetime, timedelta

import string
import uuid

class InfoScreenEntry(Base):
    __tablename__ = "infoscreen_entry"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    event_uuid = Column(UUID(as_uuid=True), ForeignKey("event.uuid"), nullable=False)
    event = relationship("Event")
    created_by_user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    created_by_user = relationship("User")

    title = Column(Text, nullable=False)
    message = Column(Text, nullable=False)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)



    def __init__(self, event, created_by_user, title: str, message: str, start_time: DateTime, end_time: DateTime):
        self.event = event
        self.created_by_user = created_by_user
        self.title = title
        self.message = message
        self.start_time = start_time
        self.end_time = end_time    

    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'event_uuid': self.event_uuid,
            'created_by_user': self.created_by_user,
            'title': self.title,
            'message': self.message,
            'start_time': self.start_time.timestamp(),
            'end_time': self.end_time.timestamp()
        }