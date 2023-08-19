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
from phoenixRest.models.core.user_consent import ConsentType

from phoenixRest.utils import randomCode

from datetime import datetime

class ConsentReversalCode(Base):
    """Represnts an code that can be used to withdraw marketing consent from an e-mail without logging in"""
    __tablename__ = "consent_reversal_code"

    code = Column(Text, nullable=False, primary_key=True)
    consent_type = Column(Enum(ConsentType), nullable=False)

    user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), primary_key=False, nullable=False)
    user = relationship("User")

    created = Column(DateTime, nullable=False)

    def __init__(self, user: User, consent_type: ConsentType):
        self.user = user
        self.code = randomCode(30)

        self.created = datetime.now()
    
    def __json__(self, request):
        return {
            'user_uuid': self.user_uuid,
            'consent_type': str(self.consent_type),
            'created': int(self.created.timestamp())
        }

