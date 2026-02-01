"""Data schema for Auth API.

This module defines Pydantic models for authentication data.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class UserRegistration(BaseModel):
    """Schema for user registration."""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class TokenRefresh(BaseModel):
    """Schema for token refresh."""

    refresh_token: str = Field(..., description="Refresh token")


class TokenData(BaseModel):
    """Schema for JWT tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class User(BaseModel):
    """Schema for user data."""

    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Schema for authentication response."""

    message: str
    user: User
    tokens: TokenData


class ProtectedData(BaseModel):
    """Schema for protected endpoint response."""

    message: str
    user: dict
    data: dict


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    error: str
    message: str
    details: Optional[list] = None
