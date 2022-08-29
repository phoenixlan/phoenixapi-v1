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
from phoenixRest.models.tickets.payment import Payment

from datetime import datetime

import uuid

class StripePayment(Base):
    __tablename__ = "stripe_payment"

    payment_uuid = Column(UUID(as_uuid=True), ForeignKey('payment.uuid'), primary_key=True)
    payment = relationship("Payment", back_populates="stripe_payment", uselist=False, foreign_keys=[payment_uuid])

    payment_id = Column(Text, nullable=False)

    paid = Column(Boolean, nullable=False)

    def __init__(self, payment: Payment, payment_id: str):
        self.payment = payment
        self.payment_id = payment_id 

        self.paid = False
       
