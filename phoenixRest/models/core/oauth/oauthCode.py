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

class OauthCode(Base):
    __tablename__ = "oauth_code"
    code = Column(Text, primary_key=True, unique=True, nullable=False)
    
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('user.uuid'), nullable=False)
    user = relationship("User", foreign_keys=[user_uuid])

    expires = Column(DateTime, nullable=False)

    def __init__(self, user: User):
        code = randomCode(10)

        self.code = code
        self.user = user
        self.expires = datetime.now() + timedelta(minutes=5)

