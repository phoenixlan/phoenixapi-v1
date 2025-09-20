from audioop import add
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

import uuid

class Location(Base):
    __tablename__ = "location"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    event_brand_uuid = Column(UUID(as_uuid=True), ForeignKey("event_brand.uuid"), nullable=True)
    event_brand = relationship("EventBrand")

    name = Column(Text, nullable=False)
    address = Column(Text, nullable=False)

    def __init__(self, name: str, address: str):
        self.name = name
        self.address = address

    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'event_brand_uuid': str(self.event_brand_uuid),
            'name': self.name,
            'address': self.address,
        }