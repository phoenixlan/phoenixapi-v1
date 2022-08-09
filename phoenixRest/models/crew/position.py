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

from phoenixRest.models import db, Base

from datetime import datetime, timedelta

import secrets
import string
import uuid

PositionAssociation = Table('user_positions', Base.metadata,
    Column('user_uuid', UUID(as_uuid=True), ForeignKey('user.uuid')),
    Column('position_uuid', UUID(as_uuid=True), ForeignKey('position.uuid'))
)

class Position(Base):
    __tablename__ = "position"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    crew_uuid = Column(UUID(as_uuid=True), ForeignKey("crew.uuid"), nullable=True)
    crew = relationship("Crew")

    team_uuid = Column(UUID(as_uuid=True), ForeignKey("team.uuid"), nullable=True)
    team = relationship("Team")

    name = Column(Text)
    description = Column(Text)
    chief = Column(Boolean, nullable=False, default=True)

    users = relationship("User",
                    secondary=PositionAssociation, back_populates="positions")

    permissions = relationship("Permission", back_populates="position")

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description


    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'name': self.name,
            'description': self.description,

            'crew': str(self.crew_uuid) if self.crew_uuid is not None else None,
            'team': str(self.team_uuid) if self.team_uuid is not None else None,
            'users': [str(user.uuid) for user in self.users],
            'chief': self.chief,
            'permissions': self.permissions

        }