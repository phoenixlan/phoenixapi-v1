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

from phoenixRest.models import Base

from phoenixRest.models.core.user import User

from phoenixRest.utils import randomCode

from datetime import datetime, timedelta

class OauthRefreshToken(Base):
    __tablename__ = "oauth_refresh_token"
    token = Column(Text, primary_key=True, unique=True, nullable=False)
    
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('user.uuid'), nullable=False)
    user = relationship("User", foreign_keys=[user_uuid])

    user_agent = Column(Text, nullable=False)

    created = Column(DateTime, nullable=False)
    expires = Column(DateTime, nullable=False)

    def __init__(self, user: User, user_agent: str):
        token = randomCode(40)

        self.token = token

        self.user = user
        self.user_agent = user_agent

        self.created = datetime.now()
        # TODO do we need to expire these?
        self.expires = datetime.now() + timedelta(days=365)
    
    def refresh(self):
        self.token = randomCode(40)

