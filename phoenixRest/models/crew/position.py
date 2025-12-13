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

import logging
log = logging.getLogger(__name__)

import uuid

class Position(Base):
    __tablename__ = "position"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    event_brand_uuid = Column(UUID(as_uuid=True), ForeignKey("event_brand.uuid"), nullable=True)
    event_brand = relationship("EventBrand")

    crew_uuid = Column(UUID(as_uuid=True), ForeignKey("crew.uuid"), nullable=True)
    crew = relationship("Crew")

    team_uuid = Column(UUID(as_uuid=True), ForeignKey("team.uuid"), nullable=True)
    team = relationship("Team")

    name = Column(Text)
    description = Column(Text)
    
    chief = Column(Boolean, nullable=False, default=False)
    is_vanity = Column(Boolean, nullable=False, server_default='False')

    position_mappings = relationship("PositionMapping", back_populates="position")

    permissions = relationship("Permission", back_populates="position")

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description


    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'event_brand_uuid': str(self.event_brand_uuid),
            'name': self.name,
            'description': self.description,
            'is_vanity': self.is_vanity,

            'crew_uuid': str(self.crew_uuid) if self.crew_uuid is not None else None,
            'team_uuid': str(self.team_uuid) if self.team_uuid is not None else None,
            'position_mappings': self.position_mappings,
            'chief': self.chief,
            'permissions': self.permissions

        }
    
    def get_title(self):
        if self.name:
            return self.name
        if self.team:
            if self.crew is None:
                raise RuntimeError("User is member of a team but not a crew?")
            return "%s i %s" % (("Lagleder av " if self.chief else "Medlem av " + self.team.name), self.crew.name)
        return "%s av %s" % (("Lagleder" if self.chief else "Medlem"), self.crew.name)

def create_or_fetch_crew_position(request, crew, team=None, chief=False):
    existing = request.db.query(Position).filter(Position.chief == chief)

    existing = existing.filter(Position.crew == crew)
    
    if team is not None:
        existing = existing.filter(Position.team == team)
    else:
        existing = existing.filter(Position.team == None)

    existing = existing.all()
    if len(existing) == 0:
        new_position = Position(None, None)
        new_position.chief = chief
        new_position.crew = crew
        new_position.team = team
        request.db.add(new_position)
        request.db.flush()
        return new_position
    elif len(existing) == 1:
        return existing[0]
    else:
        log.warn([ exist.uuid for exist in existing ])
        raise RuntimeError("More than one position exists matching the query")