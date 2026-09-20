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

class EventBrand(Base):
    __tablename__ = "event_brand"
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    events = relationship("Event", back_populates="event_brand")

    name = Column(Text, nullable=False)
    contact_email= Column(Text, nullable=False)

    def __init__(self, name: str, contact_email: str):
        self.name = name
        self.contact_email = contact_email

    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'contact_email': str(self.contact_email),
            'name': str(self.name)
        }
