# Author: richyrik

from datetime import datetime, time, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.models import Slot, SlotStatus, Turf

router = APIRouter(tags=["Seed"])

@router.post("/seed")
async def seed_db(db: AsyncSession = Depends(get_db)):
    ts = []
    for i in range(5):
        t = Turf(name=f"Turf {i}", location=f"Loc {i}")
        db.add(t)
        ts.append(t)
    
    await db.flush()

    now = datetime.now(timezone.utc).date()
    for t in ts:
        for i in range(10):
            s = Slot(
                turf_id=t.id,
                start_time=datetime.combine(now, time(8+i, 0), tzinfo=timezone.utc),
                end_time=datetime.combine(now, time(9+i, 0), tzinfo=timezone.utc),
                status=SlotStatus.AVAILABLE
            )
            db.add(s)
            
    await db.commit()
    mexwf = {"turfs": 5, "slots": 50}
    return mexwf
