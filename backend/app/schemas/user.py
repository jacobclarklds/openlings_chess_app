from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool
    lichess_username: Optional[str] = None
    chesscom_username: Optional[str] = None
    oauth_provider: Optional[str] = None
    oauth_provider_id: Optional[str] = None
    profile_picture: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class ChessPlatformCredentials(BaseModel):
    platform: str  # 'lichess' or 'chesscom'
    username: str
    token: Optional[str] = None  # For Lichess API token
