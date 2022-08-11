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

from phoenixRest.models.core.user import User
from phoenixRest.models.core.event import Event
from phoenixRest.models.crew.crew import Crew

from phoenixRest.mappers.user import map_user_with_secret_fields

from datetime import datetime, timedelta

import secrets
import string
import uuid
import enum

class ApplicationState(enum.Enum):
    created = 1
    accepted = 2
    rejected = 3


class Application(Base):
    __tablename__ = "application"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    crew_uuid = Column(UUID(as_uuid=True), ForeignKey("crew.uuid"), nullable=False)
    crew = relationship("Crew")

    event_uuid = Column(UUID(as_uuid=True), ForeignKey("event.uuid"), nullable=False)
    event = relationship("Event")

    user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    user = relationship("User", foreign_keys=[user_uuid])

    contents = Column(Text, nullable=False)

    created = Column(DateTime, nullable=False)

    # Answer from application processor
    answer = Column(Text, nullable=False)
    # Last application processor
    last_processed_by_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=True)
    last_processed_by = relationship("User", foreign_keys=[last_processed_by_uuid])

    state = Column(Enum(ApplicationState), nullable=False)

    # TODO application status

    def __init__(self, user: User, crew: Crew, event: Event, contents: str):
        self.user = user
        self.crew = crew

        self.event = event

        self.contents = contents

        self.created = datetime.now()

        self.state = ApplicationState.created
        self.answer = ""

    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'crew': self.crew,
            'event_uuid': str(self.event_uuid),
            'user': map_user_with_secret_fields(self.user, request),
            'contents': self.contents,
            'created': int(self.created.timestamp()),
            'state': str(self.state),
            'answer': None if self.state == ApplicationState.created else self.answer
        }
