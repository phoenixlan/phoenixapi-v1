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
    Table,
    JSON
)
from sqlalchemy.dialects.postgresql import UUID, ENUM

from sqlalchemy.orm import relationship

from phoenixRest.models import Base
from phoenixRest.models.core.user import User
from phoenixRest.models.core.user_consent import ConsentType

from datetime import datetime

import uuid

class AuditLog(Base):
    """Represents a log entry in the audit log, which is created whenever a user tries to perform a sensitive action
    """
    __tablename__ = "audit_log"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    action = Column(Text, nullable=False)
    meta= Column(JSON, nullable=False)

    user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), primary_key=False, nullable=False)
    user = relationship("User", foreign_keys=[user_uuid])

    created = Column(DateTime, nullable=False)

    def __init__(self, user: User, action: str, meta: dict):
        self.user = user
        self.action = action
        self.meta = meta

        self.created = datetime.now()

    
    def __json__(self, request):
        return {
            'uuid': self.uuid,
            'user_uuid': self.user_uuid,
            'action': self.action,
            'meta': self.meta,
            'created': int(self.created.timestamp())
        }
    
