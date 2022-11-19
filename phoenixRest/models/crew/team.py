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

from phoenixRest.models import Base

from phoenixRest.models.core.user import User

from datetime import datetime, timedelta

import secrets
import string
import uuid

class Team(Base):
    __tablename__ = "team"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=False)

    crew_uuid = Column(UUID(as_uuid=True), ForeignKey("crew.uuid"), nullable=False)
    crew = relationship("Crew", back_populates="teams")

    def __init__(self, crew, name: str, description: str):
        self.crew = crew
        self.name = name
        self.description = description

    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'name': self.name,
            'description': self.description,
            'crew': str(self.crew_uuid),
        }
