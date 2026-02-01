"""Data schema for Items API.

This module defines Pydantic models for item data validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    """Schema for creating a new item."""

    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: str = Field(default="", max_length=500, description="Item description")
    price: float = Field(..., ge=0, description="Item price")
    quantity: int = Field(default=0, ge=0, description="Quantity in stock")


class ItemUpdate(BaseModel):
    """Schema for updating an existing item."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, ge=0)
    quantity: Optional[int] = Field(None, ge=0)


class Item(BaseModel):
    """Schema for a complete item."""

    id: int
    name: str
    description: str
    price: float
    quantity: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginationInfo(BaseModel):
    """Schema for pagination information."""

    page: int
    limit: int
    total: int
    pages: int


class ItemListResponse(BaseModel):
    """Schema for list items response."""

    items: list[Item]
    pagination: PaginationInfo


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    error: str
    message: str
