import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Swimmer(Base):
    __tablename__ = "swimmers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    class_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
