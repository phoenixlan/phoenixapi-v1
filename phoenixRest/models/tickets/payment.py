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

from phoenixRest.models import db, Base
from phoenixRest.models.core.user import User

from datetime import datetime, timedelta

import enum
import uuid

class PaymentProvider(enum.Enum):
    vipps = 1
    stripe = 2

class PaymentState(enum.Enum):
    created = 1
    initiated = 2
    paid = 3
    failed = 4
    tickets_minted = 5

class Payment(Base):
    __tablename__ = "payment"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    user = relationship("User")

    tickets = relationship("Ticket", back_populates="payment")

    store_session_uuid = Column(UUID(as_uuid=True), ForeignKey("store_session.uuid"), nullable=True)
    store_session = relationship("StoreSession", back_populates="payment")

    vipps_payment = relationship("VippsPayment", back_populates="payment", uselist=False)
    stripe_payment = relationship("StripePayment", back_populates="payment", uselist=False)

    provider = Column(Enum(PaymentProvider), nullable=False)
    state = Column(Enum(PaymentState), nullable=False)

    price = Column(Integer, nullable=False)

    created = Column(DateTime, nullable=False)

    def __init__(self, user: User, provider: PaymentProvider, price: int):
        self.user = user
        self.provider = provider
        self.price = price

        self.state = PaymentState.created
        self.created = datetime.now()

    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'user_uuid': self.user_uuid,
            'tickets': self.tickets,
            'store_session_uuid': self.store_session_uuid,
            'provider': str(self.provider),
            'state': str(self.state),
            'price': self.price,
            'created': int(self.created.timestamp())
        }