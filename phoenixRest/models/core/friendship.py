from sqlalchemy import (
    Column,
    ForeignKey,
    DateTime
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from phoenixRest.models import Base

import uuid

from datetime import datetime

class Friendship(Base):
    __tablename__ = "friendship"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    
    source_user_uuid = (Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False))
    source_user = relationship("User", foreign_keys=[source_user_uuid])
    
    recipient_user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    recipient_user = relationship("User", foreign_keys=[recipient_user_uuid])
    
    created = Column(DateTime, nullable=False)
    
    accepted = Column(DateTime, nullable=True)
    revoked = Column(DateTime, nullable=True)
    
    
    def __init__(self, source_user, recipient_user):
        self.source_user = source_user
        self.recipient_user = recipient_user
        self.created = datetime.now()
        
    def __json__(self, request):
        return {
            "uuid": self.uuid,
            "source_user": self.source_user,
            "recipient_user": self.recipient_user,
            "accepted": int(self.accepted.timestamp()) if self.accepted is not None else None,
            "created": int(self.created.timestamp())
        }
