"""
Turf API routes.

Endpoints:
  GET /turfs              — List all turfs
  GET /turfs/{turf_id}/slots — List slots for a turf (optional date filter)
"""

from datetime import date, datetime, time, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import SlotResponse, TurfResponse
from app.core.database import get_db
from app.models.models import Slot, SlotStatus, Turf

router = APIRouter(prefix="/turfs", tags=["Turfs"])


@router.get("", response_model=list[TurfResponse])
async def list_turfs(db: AsyncSession = Depends(get_db)):
    """List all available turfs."""
    result = await db.execute(select(Turf).order_by(Turf.name))
    turfs = result.scalars().all()
    return turfs


@router.get("/{turf_id}/slots", response_model=list[SlotResponse])
async def list_slots(
    turf_id: UUID,
    slot_date: date | None = Query(
        None,
        alias="date",
        description="Filter slots by date (YYYY-MM-DD). Returns all if omitted.",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    List slots for a specific turf.

    Optionally filter by date. Only AVAILABLE slots are returned by default
    for the booking UI, but LOCKED/BOOKED slots are included for visibility.
    """
    # Verify turf exists
    turf_result = await db.execute(select(Turf).where(Turf.id == turf_id))
    turf = turf_result.scalar_one_or_none()
    if turf is None:
        raise HTTPException(status_code=404, detail=f"Turf {turf_id} not found.")

    # Build query
    query = select(Slot).where(Slot.turf_id == turf_id)

    if slot_date is not None:
        day_start = datetime.combine(slot_date, time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(slot_date, time.max, tzinfo=timezone.utc)
        query = query.where(Slot.start_time >= day_start, Slot.start_time <= day_end)

    query = query.order_by(Slot.start_time)

    result = await db.execute(query)
    slots = result.scalars().all()
    return slots
