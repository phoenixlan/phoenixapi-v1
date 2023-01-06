from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Text,
    Enum
)
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship

from phoenixRest.models import Base

from phoenixRest.models.core.user import User
from phoenixRest.models.core.event import Event

from phoenixRest.mappers.user import map_user_with_secret_fields

from datetime import datetime

import uuid
import enum

class ApplicationState(enum.Enum):
    created = 1
    accepted = 2
    rejected = 3


class Application(Base):
    __tablename__ = "application"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    event_uuid = Column(UUID(as_uuid=True), ForeignKey("event.uuid"), nullable=False)
    event = relationship("Event")

    user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    user = relationship("User", foreign_keys=[user_uuid])

    crews = relationship("ApplicationCrewMapping", order_by="ApplicationCrewMapping.list_order",
                            collection_class=ordering_list('list_order'), back_populates="application")

    contents = Column(Text, nullable=False)

    created = Column(DateTime, nullable=False)

    # Answer from application processor
    answer = Column(Text, nullable=False)

    # Last application processor
    last_processed_by_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=True)
    last_processed_by = relationship("User", foreign_keys=[last_processed_by_uuid])

    state = Column(Enum(ApplicationState), nullable=False)

    def __init__(self, user: User, crews, event: Event, contents: str):
        self.user = user

        self.crews = crews

        self.event = event

        self.contents = contents

        self.created = datetime.now()

        self.state = ApplicationState.created
        self.answer = ""

    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'crews': self.crews,
            'event': self.event,
            'user': map_user_with_secret_fields(self.user, request),
            'last_processed_by': self.last_processed_by,
            'contents': self.contents,
            'created': int(self.created.timestamp()),
            'state': str(self.state),
            'answer': None if self.state == ApplicationState.created else self.answer
        }
