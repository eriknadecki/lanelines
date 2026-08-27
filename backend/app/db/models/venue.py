import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CourseType(StrEnum):
    scy = "scy"  # short course yards (25yd) — standard for US college dual meets
    scm = "scm"  # short course meters (25m)
    lcm = "lcm"  # long course meters (50m) — championship/summer standard


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    course_type: Mapped[CourseType | None] = mapped_column(Enum(CourseType, name="course_type"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
