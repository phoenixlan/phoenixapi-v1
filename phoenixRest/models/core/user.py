"""Payment object"""
from sqlalchemy import (
    Column,
    DateTime,
    Date,
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

from phoenixRest.models.crew.position import PositionAssociation

from datetime import datetime, date

import enum
import uuid

# For passwordless test user
import os

# For hashing
import hashlib
from passlib.hash import argon2

import logging
log = logging.getLogger(__name__)

class Gender(enum.Enum):
    male = 1
    female = 2

def calculate_age(dob):
        today = date.today()
        years = today.year - dob.year
        if today.month < dob.month or (today.month == dob.month and today.day < dob.day):
            years -= 1
        return years

class User(Base):
    __tablename__ = "user"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    
    email = Column(Text, unique=True, nullable=False)
    username = Column(Text, unique=True, nullable=False)

    firstname = Column(Text, nullable=False)
    lastname = Column(Text, nullable=False)

    birthdate = Column(Date, nullable=False)
    gender = Column(Enum(Gender), nullable=False)

    phone = Column(Text, nullable=False)
    guardian_phone = Column(Text, nullable=True)

    address = Column(Text, nullable=False)
    postal_code = Column(Text, nullable=False)
    country_code = Column(Text, nullable=False, default="no")

    tos_level = Column(Integer, nullable=False, default=0)

    password = Column(Text, nullable=False)
    password_type = Column(Integer, nullable=False, default=0)

    positions = relationship("Position",
                    secondary=PositionAssociation, back_populates="users")

    created = Column(DateTime, nullable=False)

    avatar = relationship("Avatar", uselist=False, back_populates="user")

    owned_tickets = relationship("Ticket", back_populates="owner", foreign_keys="[Ticket.owner_uuid]")
    purchased_tickets = relationship("Ticket", back_populates="buyer", foreign_keys="[Ticket.buyer_uuid]")
    seatable_tickets = relationship("Ticket", back_populates="seater", foreign_keys="[Ticket.seater_uuid]")

    activation_code = relationship("ActivationCode", uselist=False, back_populates="user")

    def __init__(self, username: str, email: str, password: str,
            firstname: str, lastname: str, birthdate: date, gender: Gender,
            phone: str, address: str, postal_code: str):
        self.email = email
        self.username = username

        self.firstname = firstname
        self.lastname = lastname

        self.birthdate = birthdate
        self.gender = gender

        self.phone = phone
        self.address = address
        self.postal_code = postal_code


        self.password = argon2.hash(password)
        self.password_type = 1

        self.created = datetime.now()

    def get_avatar_urls(self, request):
        if self.avatar is None:
            api_root = request.registry.settings['api.root']
            filename = "default_child.png"
            if self.get_age() >= 16:
                if self.gender == Gender.male:
                    filename = "default_gutt.png"
                else:
                    filename = "default_jente.png"
            avatar_url = "%s/static/default_avatars/%s" % (api_root, filename)
            return {
                'sd': avatar_url,
                'hd': avatar_url,
                'thumb': avatar_url
            }
        else:
            return self.avatar.__json__(request)['urls']

    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'username': self.username,
            
            'firstname': self.firstname,
            'lastname': self.lastname,
            
            'gender': str(self.gender),

            'avatar_urls': self.get_avatar_urls(request)
        }

    def get_age(self):
        return calculate_age(self.birthdate)

    # Consider a more readable implementation
    def _constant_time_compare(val1, val2):
        if len(val1) != len(val2):
            return False
        result = 0
        for x, y in zip(val1, val2):
            result |= x ^ y
        return result == 0
        
    def _verify_type0(self, password):
        m = hashlib.sha256()
        # InfectedAPI 2.0 probably uses ASCII or norwegian ISO
        # TODO: Figure out what we need here to be 100% correct, 
        # or some people may not be able to log in
        m.update(password.encode('utf-8')) 
        hashed = m.hexdigest()
        # TODO: Timing safe compare
        return self._constant_time_compare(hashed, self.password)

    def _verify_type1(self, password):
        return argon2.verify(password, self.password)

    def _verify_type2(self, password):
        if "DEBUG" not in os.environ:
            log.error("Tried to authenticate a passwordless user in prod")
            return False
        
        log.warning("Authenticating a passwordless user!")
        return len(password) > 6

    def verify_password(self, password):
        if self.password_type == 0:
            # Sha - old password
            return self._verify_type0(password)
        elif self.password_type == 1:
            # New password type
            return self._verify_type1(password)
        elif self.password_type == 2:
            # Local development
            return self._verify_type2(password)
        else:
            log.warn("Invalid password type")
            return False
    
    def set_password(self, new_password):
        log.warn("Reset password for user %s" % self.uuid)
        self.password_type = 1
        self.password = argon2.hash(new_password)

    def migrate_password(self, password):
        if not self.verify_password(password):
            raise Exception("Failed to migrate password: it is not correct")

        self.password_type = 1
        self.password = argon2.hash(password)
        