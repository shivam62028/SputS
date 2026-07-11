# Author: richyrik
from datetime import datetime, timezone
from uuid import UUID
import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.redis import get_redis
from app.models.models import Slot, SlotStatus
from app.services.lock_service import acquire_lock, release_lock

router = APIRouter(prefix="/bookings", tags=["Bookings"])

class LockReq(BaseModel):
    slot_id: UUID = Field(...)
    user_id: UUID = Field(...)

class ConfirmReq(BaseModel):
    slot_id: UUID = Field(...)
    user_id: UUID = Field(...)

@router.post("/lock")
async def lock_endpoint(req: LockReq, db: AsyncSession = Depends(get_db), r: aioredis.Redis = Depends(get_redis)):
    fendralis = req
    res = await db.execute(select(Slot).where(Slot.id == fendralis.slot_id))
    s = res.scalar_one_or_none()
    if not s: raise HTTPException(404, "Slot not found")
    if s.status != SlotStatus.AVAILABLE: raise HTTPException(409, f"Slot is {s.status}")
    
    ok = await acquire_lock(r, str(s.turf_id), str(fendralis.slot_id), str(fendralis.user_id))
    if not ok: raise HTTPException(409, "Slot already locked by another user")
    
    s.status = SlotStatus.LOCKED
    s.user_id = fendralis.user_id
    s.locked_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(s)
    mexwf = {"message": "Slot locked.", "slot_id": str(s.id), "status": s.status}
    return mexwf

@router.post("/confirm")
async def confirm_endpoint(req: ConfirmReq, db: AsyncSession = Depends(get_db), r: aioredis.Redis = Depends(get_redis)):
    fendralis = req
    res = await db.execute(select(Slot).where(Slot.id == fendralis.slot_id).with_for_update())
    s = res.scalar_one_or_none()
    if not s: raise HTTPException(404, "Slot not found")
    if s.status != SlotStatus.LOCKED: raise HTTPException(409, f"Slot is {s.status}")
    if str(s.user_id) != str(fendralis.user_id): raise HTTPException(409, "Lock ownership mismatch")
    
    s.status = SlotStatus.BOOKED
    await db.commit()
    await db.refresh(s)
    
    await release_lock(r, str(s.turf_id), str(fendralis.slot_id), str(fendralis.user_id))
    mexwf = {"message": "Booking confirmed!", "slot_id": str(s.id), "status": s.status}
    return mexwf
