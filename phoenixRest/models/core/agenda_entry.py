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

from phoenixRest.models.core.user import User
from phoenixRest.models.core.event import Event

from datetime import datetime, timedelta

import string
import uuid

class AgendaEntry(Base):
    __tablename__ = "agenda_entry"
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    event_uuid = Column(UUID(as_uuid=True), ForeignKey("event.uuid"), nullable=False)
    event = relationship("Event")
    
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    location = Column(Text, nullable=True, server_default=None)
    time = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=True)

    deviating_time = Column(DateTime, nullable=True, server_default=None)
    deviating_time_unknown = Column(Boolean, server_default='false')
    deviating_location = Column(Text, nullable=True, server_default=None)
    deviating_information = Column(Text, nullable=True, server_default=None)

    pinned = Column(Boolean, server_default='false')
    cancelled = Column(Boolean, server_default='false')

    created_by_user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    created_by_user = relationship("User", foreign_keys=[created_by_user_uuid])
    modified_by_user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=True, server_default=None)
    modified_by_user = relationship("User", foreign_keys=[modified_by_user_uuid])
    
    created = Column(DateTime, nullable=False, server_default='NOW()')
    modified = Column(DateTime, nullable=True, server_default=None)

    def __init__(self, event: Event, title: str, description: str, location: str, time: DateTime, duration: int, pinned: bool, created_by_user: User):
        self.event = event
        self.title = title
        self.description = description
        self.location = location
        self.time = time
        self.duration = duration
        self.pinned = pinned
        self.created = datetime.now()
        self.created_by_user = created_by_user

    def __json__(self, request):
        data = {
            'uuid': str(self.uuid),
            'event_uuid': self.event_uuid,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'time': int(self.time.timestamp()) if self.time is not None else None,
            'duration': self.duration,
            'deviating_time': int(self.deviating_time.timestamp()) if self.deviating_time is not None else None,
            'deviating_time_unknown': self.deviating_time_unknown,
            'deviating_location': self.deviating_location,
            'deviating_information': self.deviating_information,
            'pinned': self.pinned,
            'cancelled': self.cancelled,
            'created_by_user_uuid': self.created_by_user_uuid,
            'created': int(self.created.timestamp()),
            'modified_by_user_uuid': self.modified_by_user_uuid,
            'modified': int(self.modified.timestamp()) if self.modified is not None else None
        }

        return data