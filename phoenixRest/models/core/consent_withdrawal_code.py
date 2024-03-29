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
from sqlalchemy.dialects.postgresql import UUID, ENUM

from sqlalchemy.orm import relationship

from phoenixRest.models import Base
from phoenixRest.models.core.user import User
from phoenixRest.models.core.user_consent import ConsentType

from datetime import datetime

import uuid

class ConsentWithdrawalCode(Base):
    """Represnts a code that can be used to withdraw marketing consent from an e-mail without logging in"""
    __tablename__ = "consent_withdrawal_code"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    consent_type = Column(ENUM(ConsentType, create_type=False), nullable=False)

    user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), primary_key=False, nullable=False)
    user = relationship("User", foreign_keys=[user_uuid])

    created = Column(DateTime, nullable=False)

    def __init__(self, user: User, consent_type: ConsentType):
        self.user = user
        self.consent_type = consent_type
        self.created = datetime.now()
    
    def __json__(self, request):
        return {
            'user_uuid': self.user_uuid,
            'consent_type': str(self.consent_type),
            'created': int(self.created.timestamp())
        }
    
    def get_withdrawal_url(self, request):
        return "%s/static/withdrawConsent.html?uuid=%s" % (request.registry.settings["api.root"], self.uuid)

