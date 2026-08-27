import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Swimmer(Base):
    __tablename__ = "swimmers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    # Free-form class standing (FR/SO/JR/SR/GR, "5th year", etc.) rather than
    # a strict enum — roster CSVs from different schools spell this
    # differently, and there's no real need to normalize it.
    class_standing: Mapped[str | None] = mapped_column(String(10), nullable=True)
