from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship

from phoenixRest.models import Base

from phoenixRest.models.core.user import User

from phoenixRest.features.discord import discord_get_user, discord_refresh_tokens, discord_username_from_obj

from datetime import datetime, timedelta

import logging
log = logging.getLogger(__name__)

class DiscordMapping(Base):
    __tablename__ = "discord_mapping"

    discord_id = Column(Text, nullable=False, primary_key=True)

    user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False, primary_key=True)
    user = relationship("User", back_populates="discord_mapping")

    discord_refresh_token = Column(Text, nullable=False)
    discord_access_token = Column(Text, nullable=False)
    discord_access_token_expiry = Column(DateTime, nullable=False)

    discord_username = Column(Text, nullable=False)
    discord_username_last_check = Column(DateTime, nullable=False)

    created = Column(DateTime, nullable=False)

    def __init__(self, user: User, discord_id: str, discord_refresh_token: str, discord_access_token: str, discord_access_token_expiry_delta: int):
        self.user = user
        self.discord_id = discord_id
        self.discord_refresh_token = discord_refresh_token
        self.discord_access_token = discord_access_token

        self.created = datetime.now()
        self.discord_access_token_expiry = datetime.now() + timedelta(seconds=discord_access_token_expiry_delta - 10)

        user_obj = discord_get_user(self.discord_access_token)
        self.discord_username = discord_username_from_obj(user_obj)
        self.discord_username_last_check = datetime.now()

    def __json__(self, request):
        if datetime.now() > self.discord_access_token_expiry:
            log.info("Fetched a new discord access token since the old one was expired")
            tokens = discord_refresh_tokens(self.discord_refresh_token)
            self.discord_access_token = tokens['access_token']
            self.discord_access_token_expiry = datetime.now() + timedelta(seconds=tokens['expires_in']-10)
            self.discord_refresh_token = tokens['refresh_token']

        if datetime.now() > self.discord_username_last_check + timedelta(minutes=5):
            log.info("Fetching discord username again")
            user_obj = discord_get_user(self.discord_access_token)
            self.discord_username = discord_username_from_obj(user_obj)
            self.discord_username_last_check = datetime.now()
        else:
            log.info("Using cached Discord username")

        return {
            "discord_id": self.discord_id,
            "username": self.discord_username
        }
        