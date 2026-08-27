import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class MeetType(StrEnum):
    dual = "dual"
    tri = "tri"
    championship = "championship"


class MeetStatus(StrEnum):
    scheduled = "scheduled"
    live = "live"
    completed = "completed"


class MeetEventStatus(StrEnum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"


class Meet(Base):
    __tablename__ = "meets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    home_team_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    away_team_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    meet_type: Mapped[MeetType] = mapped_column(Enum(MeetType, name="meet_type"))
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[MeetStatus] = mapped_column(Enum(MeetStatus, name="meet_status"), default=MeetStatus.scheduled)
    venue_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MeetEvent(Base):
    __tablename__ = "meet_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("meets.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    event_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[MeetEventStatus] = mapped_column(
        Enum(MeetEventStatus, name="meet_event_status"), default=MeetEventStatus.scheduled
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
