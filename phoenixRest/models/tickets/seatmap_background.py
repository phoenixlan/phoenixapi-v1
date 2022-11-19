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

from phoenixRest.models.tickets.ticket import Ticket

import uuid

class SeatmapBackground(Base):
    __tablename__ = "seatmap_background"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)

    created = Column(DateTime, nullable=False, server_default='NOW()')
    extension = Column(Text, nullable=False)

    uploader_uuid = Column(UUID(as_uuid=True), ForeignKey("user.uuid"), nullable=False)
    uploader = relationship("User", foreign_keys=[uploader_uuid])

    def __init__(self, uploader, extension: str):
        self.uploader = uploader
        self.extension = extension

    def get_url(self, request):
        api_root = request.registry.settings['api.root']
        seatmap_path = "files%s" % (request.registry.settings['ticket.seatmap_background_location'].replace(request.registry.settings['files.static_view_root'], ''))
        filename = "%s.%s" % (str(self.uuid), self.extension)
        return "%s/%s/%s" % ( api_root, seatmap_path, filename )
    
    def get_fs_location(self, request):
        filename = "%s.%s" % (str(self.uuid), self.extension)
        return "%s/%s" % ( request.registry.settings['ticket.seatmap_background_location'], filename)

    def __json__(self, request):
        return {
            'uuid': str(self.uuid),
            'uploader_uuid': self.uploader_uuid,
            'created': int(self.created.timestamp()),
            'url': self.get_url(request)
        }