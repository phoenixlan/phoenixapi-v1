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

from datetime import datetime

class PasswordResetCode(Base):
    __tablename__ = "password_reset_code"

    code = Column(Text, nullable=False, primary_key=True)
    client_id = Column(Text, nullable=False)

    user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), primary_key=False, nullable=False)
    user = relationship("User")

    created = Column(DateTime, nullable=False)

    def __init__(self, user: User, client_id: str):
        self.user = user
        self.code = randomCode(30)
        self.client_id = client_id

        self.created = datetime.now()
    
    def __json__(self, request):
        return {
            'user_uuid': self.user_uuid,
            'created': int(self.created.timestamp())
        }
