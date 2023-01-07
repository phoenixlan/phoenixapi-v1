from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Integer,
    Boolean
)
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship

from phoenixRest.models import Base

from datetime import datetime

import logging
log = logging.getLogger(__name__)

import uuid

class ApplicationCrewMapping(Base):
    __tablename__ = "application_crew_mapping"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    application_uuid = Column(UUID(as_uuid=True), ForeignKey("application.uuid"), nullable=False)
    application = relationship("Application", back_populates="crews", uselist=False)

    crew_uuid = Column(UUID(as_uuid=True), ForeignKey("crew.uuid"), nullable=False)
    crew = relationship("Crew")

    list_order = Column(Integer, nullable=False)
    accepted = Column(Boolean, nullable=False, server_default='false')

    created = Column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint('application_uuid', 'crew_uuid', 'list_order', name='_application_crew_mapping_uic'),
    )

    def __init__(self, crew):
        self.crew = crew
        self.created = datetime.now()
    
    def __json__(self, request):
        return {
            'uuid': self.uuid,
            'application_uuid': self.application_uuid,
            'crew': self.crew,
            'list_order': self.list_order,
            'created': int(self.created.timestamp()),
            "accepted": self.accepted
        }
