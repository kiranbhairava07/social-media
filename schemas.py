from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional

# ============================================
# USER SCHEMAS
# ============================================
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# QR CODE SCHEMAS
# ============================================
class QRCodeCreate(BaseModel):
    code: str = Field(min_length=3, max_length=100, pattern=r'^[a-zA-Z0-9\-_]+$')
    target_url: str = Field(min_length=1, max_length=2000)


class QRCodeUpdate(BaseModel):
    target_url: Optional[str] = Field(None, min_length=1, max_length=2000)
    is_active: Optional[bool] = None


class QRCodeResponse(BaseModel):
    id: int
    code: str
    target_url: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    scan_count: int = 0  # Will be populated separately

    model_config = ConfigDict(from_attributes=True)


# ============================================
# QR SCAN SCHEMAS
# ============================================
class QRScanCreate(BaseModel):
    qr_code_id: int
    source: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class QRScanResponse(BaseModel):
    id: int
    qr_code_id: int
    scanned_at: datetime
    source: Optional[str]
    ip_address: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# ============================================
# ANALYTICS SCHEMAS
# ============================================
class QRAnalytics(BaseModel):
    qr_code_id: int
    total_scans: int
    scans_today: int
    scans_this_week: int
    scans_this_month: int
    recent_scans: list[QRScanResponse]


# ============================================
# AUTH SCHEMAS
# ============================================
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None