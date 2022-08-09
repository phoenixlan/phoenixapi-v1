"""Payment object"""
from email.policy import default
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    Text,
    Boolean,
    Enum,
    Table
)
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship

from phoenixRest.models import db
from phoenixRest.models import Base

from phoenixRest.models.core.user import User
from phoenixRest.mappers.seatmap_background import map_seatmap_background_no_metadata

# We must make sure that classes that are used in relationships are loaded
from phoenixRest.models.tickets.row import Row

from datetime import datetime, timedelta

import secrets
import string
import uuid

class Seatmap(Base):
    __tablename__ = "seatmap"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    name = Column(Text, nullable=False)
    description = Column(Text, nullable=False)

    background_uuid = Column(UUID(as_uuid=True), ForeignKey("seatmap_background.uuid"), nullable=True)
    background = relationship("SeatmapBackground")

    width = Column(Integer, server_default="600")
    height = Column(Integer, server_default="800")

    rows = relationship("Row", back_populates="seatmap")

    events = relationship("Event", back_populates="seatmap")

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description


    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'name': str(self.name),
            'description': str(self.description),
            'background': map_seatmap_background_no_metadata(self.background, request) if self.background is not None else None,
            'events': self.events,
            'rows': self.rows,
            'width': self.width,
            'height': self.height
        }
