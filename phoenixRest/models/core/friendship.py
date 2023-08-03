from sqlalchemy import (
    Column,
    ForeignKey,
    DateTime
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from phoenixRest import Base

import uuid

from datetime import datetime

class Friendship(Base):
    __tablename__ = "friendship"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    
    source_user_uuid = (Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False))
    source_user = relationship("User", foreign_keys=[source_user_uuid])
    
    recipient_user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    recipient_user = relationship("User", foreign_keys=[recipient_user_uuid])
    
    accepted = Column(DateTime, nullable=False)
    
    revoked = Column(DateTime, nullable=False)
    
    created = Column(DateTime)
    
    def __init__(self, source_user, recipient_user, accepted, revoked):
        self.source_user = source_user
        self.recipient_user = recipient_user
        self.created = datetime.now()
        self.accepted = accepted
        self.revoked = revoked
        
    def __json__(self, request):
        return {
            "uuid": self.uuid,
            "recipient_user": self.recipient_user,
            "accepted": int(self.accepted.timestamp()) if self.accepted is not None else None,
            "revoked": int(self.revoked.timestamp()) if self.revoked is not None else None,
            "created": int(self.created.timestamp()),
        }