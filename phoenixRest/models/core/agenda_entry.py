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

from phoenixRest.models.core.event import Event

from datetime import datetime, timedelta

import string
import uuid

class AgendaEntry(Base):
    __tablename__ = "agenda_entry"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    event_uuid = Column(UUID(as_uuid=True), ForeignKey("event.uuid"), nullable=False)
    event = relationship("Event")
    
    time = Column(DateTime, nullable=False)

    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)

    def __init__(self, title: str, description: str, time: datetime, event: Event):
        self.title = title
        self.description = description
        self.event = event
        self.time = time

    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'title': self.title,
            'description': self.description,
            'time': int(self.time.timestamp()),
            'event_uuid': self.event_uuid
        }