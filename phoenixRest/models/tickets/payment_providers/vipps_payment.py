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
from phoenixRest.models.tickets.payment import Payment

import string
import secrets

def generateSlug():
    # TODO make this collision safe. The chance of a collision is already 1:54^6, but hey.
    s = ""
    for i in range(0,4):
        s += string.ascii_letters[secrets.randbelow(len(string.ascii_letters))]
    s += "-"
    for i in range(0,4):
        s += string.ascii_letters[secrets.randbelow(len(string.ascii_letters))]
    return s

class VippsPayment(Base):
    __tablename__ = "vipps_payment"

    payment_uuid = Column(UUID(as_uuid=True), ForeignKey('payment.uuid'), primary_key=True)
    payment = relationship("Payment", back_populates="vipps_payment", uselist=False, foreign_keys=[payment_uuid])

    slug = Column(Text, nullable=False, unique=True)

    order_id = Column(Text, nullable=True)

    state = Column(Text, nullable=False)

    def __init__(self, payment: Payment):
        self.payment = payment
        self.slug = generateSlug()

        self.state = "NOT_SET"
       
