from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship

from phoenixRest.models import Base

from phoenixRest.models.core.user import User

from phoenixRest.utils import randomCode

from datetime import datetime, timedelta

"""
Stores the oauth state variable we pass to discord and later receive back

One-time use when user returns from the Discord OAuth flow, should be burnt after use
"""
class DiscordMappingOauthState(Base):
    __tablename__ = "discord_mapping_oauth_state"
    code = Column(Text, primary_key=True, unique=True, nullable=False)
    
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('user.uuid'), nullable=False)
    user = relationship("User", foreign_keys=[user_uuid])

    created = Column(DateTime, nullable=False)

    def __init__(self, user: User):
        code = randomCode(20)

        self.code = code
        self.user = user
        self.created = datetime.now()

    def has_expired(self):
        return datetime.now() > self.created + timedelta(minutes=5)

