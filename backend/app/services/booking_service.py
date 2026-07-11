"""
Booking service — core business logic for the two-phase booking flow.

Phase A (lock_slot):
    1. Validate slot exists & is AVAILABLE
    2. Acquire Redis distributed lock (NX EX 300)
    3. Update DB: status → LOCKED, assign user_id

Phase B (confirm_booking):
    1. Verify Redis lock is still held by the requesting user
    2. SELECT ... FOR UPDATE (pessimistic DB lock)
    3. Verify slot status == LOCKED & user matches
    4. Update DB: status → BOOKED
    5. Release Redis lock
    6. Commit transaction

Defense-in-depth:
    Redis provides fast cross-instance mutual exclusion.
    PostgreSQL SELECT FOR UPDATE provides ACID guarantees on final write.
"""

from datetime import datetime, timezone
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Slot, SlotStatus
from app.services import lock_service


class BookingError(Exception):
    """Base exception for booking failures."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class SlotNotFoundError(BookingError):
    """Raised when the requested slot does not exist."""

    def __init__(self, slot_id: str):
        super().__init__(f"Slot {slot_id} not found.", status_code=404)


class SlotUnavailableError(BookingError):
    """Raised when the slot is already locked or booked."""

    def __init__(self, slot_id: str, current_status: str):
        super().__init__(
            f"Slot {slot_id} is currently {current_status}. Cannot lock.",
            status_code=409,
        )


class LockConflictError(BookingError):
    """Raised when the Redis lock cannot be acquired (another user holds it)."""

    def __init__(self, slot_id: str):
        super().__init__(
            f"Slot {slot_id} is already locked by another user.",
            status_code=409,
        )


class LockExpiredError(BookingError):
    """Raised when the lock has expired before confirmation."""

    def __init__(self, slot_id: str):
        super().__init__(
            f"Lock for slot {slot_id} has expired. Please try again.",
            status_code=409,
        )


class LockOwnershipError(BookingError):
    """Raised when the confirming user does not own the lock."""

    def __init__(self, slot_id: str):
        super().__init__(
            f"You do not hold the lock for slot {slot_id}.",
            status_code=409,
        )


# ═══════════════════════════════════════════════════════════════
#  PHASE A — Lock a Slot
# ═══════════════════════════════════════════════════════════════

async def lock_slot(
    db: AsyncSession,
    redis: aioredis.Redis,
    slot_id: UUID,
    user_id: UUID,
) -> Slot:
    """
    Acquire a distributed lock on a slot and mark it as LOCKED in the DB.

    Raises:
        SlotNotFoundError:   If the slot doesn't exist.
        SlotUnavailableError: If the slot is not AVAILABLE.
        LockConflictError:   If another user already holds the Redis lock.
    """
    slot_id_str = str(slot_id)
    user_id_str = str(user_id)

    # 1. Fetch slot from DB
    result = await db.execute(select(Slot).where(Slot.id == slot_id))
    slot = result.scalar_one_or_none()

    if slot is None:
        raise SlotNotFoundError(slot_id_str)

    if slot.status != SlotStatus.AVAILABLE:
        raise SlotUnavailableError(slot_id_str, slot.status.value)

    # 2. Attempt Redis lock (atomic NX + EX)
    acquired = await lock_service.acquire_lock(redis, slot_id_str, user_id_str)

    if not acquired:
        raise LockConflictError(slot_id_str)

    # 3. Lock acquired → update DB state
    try:
        slot.status = SlotStatus.LOCKED
        slot.user_id = user_id
        slot.locked_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(slot)
    except Exception:
        # If DB update fails, release the Redis lock to stay consistent
        await lock_service.release_lock(redis, slot_id_str, user_id_str)
        await db.rollback()
        raise

    return slot


# ═══════════════════════════════════════════════════════════════
#  PHASE B — Confirm a Booking
# ═══════════════════════════════════════════════════════════════

async def confirm_booking(
    db: AsyncSession,
    redis: aioredis.Redis,
    slot_id: UUID,
    user_id: UUID,
) -> Slot:
    """
    Finalize a booking: verify lock ownership, write BOOKED to DB, release lock.

    Uses SELECT ... FOR UPDATE to prevent any concurrent modification
    during the final status transition.

    Raises:
        SlotNotFoundError:    If the slot doesn't exist.
        LockExpiredError:     If the Redis lock expired before confirmation.
        LockOwnershipError:   If the confirming user doesn't own the lock.
    """
    slot_id_str = str(slot_id)
    user_id_str = str(user_id)

    # 1. Check Redis lock ownership
    lock_owner = await lock_service.get_lock_owner(redis, slot_id_str)

    if lock_owner is None:
        raise LockExpiredError(slot_id_str)

    if lock_owner != user_id_str:
        raise LockOwnershipError(slot_id_str)

    # 2. Begin strict DB transaction with row-level lock
    result = await db.execute(
        select(Slot)
        .where(Slot.id == slot_id)
        .with_for_update()  # SELECT ... FOR UPDATE — pessimistic lock
    )
    slot = result.scalar_one_or_none()

    if slot is None:
        raise SlotNotFoundError(slot_id_str)

    if slot.status != SlotStatus.LOCKED:
        raise BookingError(
            f"Slot {slot_id_str} is in unexpected state '{slot.status.value}'. Expected LOCKED.",
            status_code=409,
        )

    if str(slot.user_id) != user_id_str:
        raise LockOwnershipError(slot_id_str)

    # 3. Transition to BOOKED
    slot.status = SlotStatus.BOOKED
    await db.commit()
    await db.refresh(slot)

    # 4. Release the Redis lock (no longer needed)
    await lock_service.release_lock(redis, slot_id_str, user_id_str)

    return slot
