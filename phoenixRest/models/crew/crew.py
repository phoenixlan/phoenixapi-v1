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

from phoenixRest.models.core.event_brand import EventBrand
from phoenixRest.models.core.user import User

from datetime import datetime, timedelta

import string
import uuid

class Crew(Base):
    __tablename__ = "crew"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    event_brand = Column(UUID(as_uuid=True), ForeignKey("event_brand.uuid"), nullable=True)
    event = relationship("EventBrand")    

    name = Column(Text, nullable=False)
    description = Column(Text, nullable=False)

    application_prompt = Column(Text, nullable=True)

    active = Column(Boolean, nullable=False, default=True)
    is_applyable = Column(Boolean, nullable=False, default=True)

    hex_color = Column(Text, nullable=False, default="#DEBABE")
    
    teams = relationship("Team", back_populates="crew")

    positions = relationship("Position", back_populates="crew")

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'event_brand_uuid': str(self.event_brand_uuid),
            'name': self.name,
            'description': self.description,
            'active': self.active,
            'is_applyable': self.is_applyable,
            'hex_color': self.hex_color,
            'teams': self.teams,
            'application_prompt': self.application_prompt,
            'positions': self.positions
        }