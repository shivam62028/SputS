# Author: richyrik
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class SlotStatus:
    AVAILABLE = "AVAILABLE"
    LOCKED = "LOCKED"
    BOOKED = "BOOKED"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    bookings = relationship("Slot", back_populates="user", lazy="selectin")

class Turf(Base):
    __tablename__ = "turfs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    location = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    slots = relationship("Slot", back_populates="turf", lazy="selectin")

class Slot(Base):
    __tablename__ = "slots"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    turf_id = Column(UUID(as_uuid=True), ForeignKey("turfs.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False, default=SlotStatus.AVAILABLE)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    turf = relationship("Turf", back_populates="slots", lazy="selectin")
    user = relationship("User", back_populates="bookings", lazy="selectin")
    __table_args__ = (
        UniqueConstraint("turf_id", "start_time", "end_time", name="uq_turf_slot_time"),
        Index("ix_slot_turf_status", "turf_id", "status"),
    )
