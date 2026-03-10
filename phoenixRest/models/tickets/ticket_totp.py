
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
    Table,
    Identity
)
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship

from phoenixRest.models import Base

from datetime import datetime, timedelta

import secrets
import base64

def gen_totp():
    return base64.b32encode(secrets.token_bytes(nbytes=20)).decode("ascii")

class TicketTotp(Base):
    """Enables some additional protection against ticket abuse"""
    __tablename__ = "ticket_totp"
    ticket_id = Column(Integer, ForeignKey("ticket.ticket_id"), nullable=False, primary_key=True)
    ticket = relationship("Ticket", back_populates="totp")

    totp= Column(Text, nullable=False, default=gen_totp)

    created = Column(DateTime, nullable=False, default=datetime.now)

    def __init__(self, ticket):
        self.ticket = ticket

