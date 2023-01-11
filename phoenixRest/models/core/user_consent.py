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

import enum

from datetime import datetime

class ConsentType(enum.Enum):
    event_notification = 1

class UserConsent(Base):
    __tablename__ = "user_consent"

    user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), primary_key=True, nullable=False)
    user = relationship("User", back_populates="consents")

    consent_type = Column(Enum(ConsentType), nullable=False, primary_key=True)
    source = Column(Text, nullable=False)

    created = Column(DateTime, nullable=False)

    def __init__(self, user: User, consent_type: ConsentType, source: str):
        self.user = user
        self.consent_type = consent_type
        self.source = source

        self.created = datetime.now()
    
    def __json__(self, request):
        return {
            'consent_type': str(self.consent_type),
            'source': self.source,
            'created': int(self.created.timestamp())
        }
