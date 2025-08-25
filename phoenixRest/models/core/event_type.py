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
from sqlalchemy import and_

from phoenixRest.models import Base

import logging
log = logging.getLogger(__name__)

import uuid

class EventType(Base):
    __tablename__ = "event_type"
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    name = Column(Text, nullable=False)

    def __init__(self, name: str):
        self.name = name

    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'name': str(self.name)
        }