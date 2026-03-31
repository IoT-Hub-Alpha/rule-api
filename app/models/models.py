from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from ..db.db import Base
from ..core.settings import settings


def _uuid_column_type():
    if settings.database_url.startswith("postgres"):
        return PG_UUID(as_uuid=False)
    return String(36)


UUID_COLUMN = _uuid_column_type()


class Rule(Base):
    __tablename__ = "rules"

    id = Column(UUID_COLUMN, primary_key=True, default=lambda: str(uuid4()))
    device_id = Column(UUID_COLUMN, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    condition = Column(JSON, nullable=False)
    action_config = Column(JSON, nullable=False)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    event_cooldown_until = Column(DateTime(timezone=True), nullable=True)
    is_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
