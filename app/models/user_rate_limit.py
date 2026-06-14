from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
)

from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

class UserRateLimit(Base):
    __tablename__ = "user_rate_limit"

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        primary_key=True
    )

    count = Column(Integer, default=0)
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(Text, nullable=True)
    banned_until = Column(DateTime, nullable=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow
    )
