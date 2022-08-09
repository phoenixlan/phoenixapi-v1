"""Payment object"""
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

from datetime import datetime, timedelta

import secrets
import string
import uuid

class Entrance(Base):
    __tablename__ = "entrance"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    name = Column(Text, nullable=False)

    def __init__(self, name: str):
        self.name = name


    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'name': self.name
        }
