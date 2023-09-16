from sqlalchemy import (
    Column,
    ForeignKey,
    DateTime,
    Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from datetime import datetime
import uuid
import enum

class OrderStates(enum.Enum):
    created     = "CREATED" # Placed?
    in_progress = "IN PROGRESS"
    finished    = "FINISHED"
    
from phoenixRest.models import Base

class CardOrder(Base):
    __tablename__ = "card_order"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    
    subject_user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    subject_user = relationship("User", foreign_keys=subject_user_uuid)
    
    creator_user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    creator_user = relationship("User", foreign_keys=creator_user_uuid)
    
    updated_by_user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=True)
    updated_by_user = relationship("User", foreign_keys=updated_by_user_uuid)
    
    last_updated = Column(DateTime, nullable=True)
    
    created = Column(DateTime, nullable=False)
    
    state = Column(Enum(OrderStates), server_default=(OrderStates.created.value), nullable=False)
    
    def __init__(self, subject_user, creator_user):
        self.subject_user = subject_user
        self.creator_user = creator_user
        self.created = datetime.now()
    
    def __json__(self, request):
        return {
            "uuid": self.uuid,
            "subject_user": self.subject_user,
            "creator_user": self.creator_user,
            "updated_by_user": self.updated_by_user,
            "last_updated": int(self.last_updated.timestamp()),
            "created": int(self.created.timestamp()),
            "state": self.state
        }