from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserRateLimitBase(BaseModel):
    count: int = 0
    is_banned: bool = False
    ban_reason: Optional[str] = None
    banned_until: Optional[datetime] = None


class UserRateLimitCreate(UserRateLimitBase):
    user_id: int


class UserRateLimitUpdate(BaseModel):
    count: Optional[int] = None
    is_banned: Optional[bool] = None
    ban_reason: Optional[str] = None
    banned_until: Optional[datetime] = None


class UserRateLimitResponse(UserRateLimitBase):
    user_id: int
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2
