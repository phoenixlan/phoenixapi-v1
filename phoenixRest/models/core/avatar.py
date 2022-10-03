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

from phoenixRest.models.core.user import User

from datetime import datetime, timedelta

import enum
import uuid

class AvatarState(enum.Enum):
    uploaded = 1
    accepted = 2
    rejected = 3


class Avatar(Base):
    __tablename__ = "avatar"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    state = Column(Enum(AvatarState), nullable=False)

    user_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=True)
    user = relationship("User", back_populates="avatar")

    created = Column(DateTime, nullable=False)

    extension = Column(Text, nullable=False)

    def __init__(self, user: User, extension: str):
        self.user = user
        self.created = datetime.now()
        self.state = AvatarState.uploaded
        self.extension = extension


    def __json__(self, request):
        sd_dir = request.registry.settings["avatar.directory_sd"]
        hd_dir = request.registry.settings["avatar.directory_hd"]
        thumb_dir = request.registry.settings["avatar.directory_thumb"]

        api_root = request.registry.settings['api.root']
        
        avatar_dict = {
            'uuid': self.uuid,
            'user': self.user,
            #'created': int(self.created.timestamp()),
            'state': str(self.state),
            'urls': {
                'sd': "%s%s/%s.%s" % (api_root, sd_dir, self.uuid, self.extension),
                'hd': "%s%s/%s.%s" % (api_root, hd_dir, self.uuid, self.extension),
                'thumb': "%s%s/%s.%s" % (api_root, thumb_dir, self.uuid, self.extension)
            }
        }

        return avatar_dict
