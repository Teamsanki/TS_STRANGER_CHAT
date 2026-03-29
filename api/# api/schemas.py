from pydantic import BaseModel
from typing import Optional


class TelegramAuthRequest(BaseModel):
    init_data: str


class FindPartnerRequest(BaseModel):
    telegram_id: int
    premium: Optional[bool] = False


class EndChatRequest(BaseModel):
    telegram_id: int


class UserProfileResponse(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    premium: bool = False
    premium_expiry: Optional[str] = None
    status: str = "idle"
