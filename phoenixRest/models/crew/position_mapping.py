
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship

from phoenixRest.models import Base

from datetime import datetime

import logging
log = logging.getLogger(__name__)

import uuid

class PositionMapping(Base):
    __tablename__ = "user_positions"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    event_brand_uuid = Column(UUID(as_uuid=True), ForeignKey("event_brand.uuid"), nullable=True)
    event_brand = relationship("EventBrand")

    position_uuid = Column(UUID(as_uuid=True), ForeignKey("position.uuid"), nullable=False)
    position = relationship("Position", back_populates="position_mappings", uselist=False)

    user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    user = relationship("User", back_populates="position_mappings", uselist=False)

    event_uuid = Column(UUID(as_uuid=True), ForeignKey("event.uuid"), nullable=True)
    event = relationship("Event")

    created = Column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint('position_uuid', 'user_uuid', 'event_uuid', name='_user_positionmapping_uic'),
    )

    def __init__(self, user, position, event=None):
        self.user = user
        self.position = position
        self.event = event
        self.created = datetime.now()
    
    def __json__(self, request):
        return {
            'uuid': self.uuid,
            'event_brand_uuid': str(self.event_brand_uuid),
            'position_uuid': self.position_uuid,
            'user_uuid': self.user_uuid,
            'event_uuid': self.event_uuid,
            'created': int(self.created.timestamp())
        }
