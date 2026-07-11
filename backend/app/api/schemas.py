"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ═══════════════════════════════════════════════════════════════
#  User Schemas
# ═══════════════════════════════════════════════════════════════

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
#  Turf Schemas
# ═══════════════════════════════════════════════════════════════

class TurfResponse(BaseModel):
    id: UUID
    name: str
    location: str
    description: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
#  Slot Schemas
# ═══════════════════════════════════════════════════════════════

class SlotResponse(BaseModel):
    id: UUID
    turf_id: UUID
    start_time: datetime
    end_time: datetime
    status: str
    user_id: UUID | None = None
    locked_at: datetime | None = None
    updated_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
#  Booking Schemas
# ═══════════════════════════════════════════════════════════════

class LockRequest(BaseModel):
    """Request body for POST /bookings/lock"""
    slot_id: UUID = Field(..., description="UUID of the slot to lock")
    user_id: UUID = Field(..., description="UUID of the user requesting the lock")


class ConfirmRequest(BaseModel):
    """Request body for POST /bookings/confirm"""
    slot_id: UUID = Field(..., description="UUID of the locked slot to confirm")
    user_id: UUID = Field(..., description="UUID of the user confirming the booking")


class BookingResponse(BaseModel):
    """Response for booking operations"""
    message: str
    slot: SlotResponse


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
