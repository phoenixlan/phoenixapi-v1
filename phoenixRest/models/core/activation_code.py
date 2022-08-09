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

from phoenixRest.models import db
from phoenixRest.models import Base
from phoenixRest.models.core.user import User

from phoenixRest.utils import randomCode

from datetime import datetime

class ActivationCode(Base):
    __tablename__ = "activation_code"

    user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), primary_key=True, nullable=False)
    user = relationship("User", back_populates="activation_code")

    code = Column(Text, nullable=False, primary_key=True)
    client_id = Column(Text, nullable=True)

    created = Column(DateTime, nullable=False)

    def __init__(self, user: User, client_id: str):
        self.user = user
        self.code = randomCode(30)
        self.client_id = client_id

        self.created = datetime.now()
