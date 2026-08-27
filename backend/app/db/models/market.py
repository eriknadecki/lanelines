import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class MarketGroupStatus(StrEnum):
    open = "open"
    closed = "closed"
    resolved = "resolved"


class MarketStatus(StrEnum):
    open = "open"
    paused = "paused"
    closed = "closed"
    resolved = "resolved"


class MarketOutcome(StrEnum):
    yes = "yes"
    no = "no"


class MarketGroup(Base):
    __tablename__ = "market_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    meet_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("meets.id"), nullable=True)
    meet_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meet_events.id"), nullable=True
    )
    close_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[MarketGroupStatus] = mapped_column(
        Enum(MarketGroupStatus, name="market_group_status"), default=MarketGroupStatus.open
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    markets: Mapped[list["Market"]] = relationship(back_populates="market_group", order_by="Market.created_at")


class Market(Base):
    __tablename__ = "markets"
    __table_args__ = (
        # DB-enforced guarantee that at most one market per group can ever
        # resolve YES, so "exactly one winner" can't be violated by an
        # application bug racing two resolution calls.
        Index(
            "ix_markets_one_winner_per_group",
            "market_group_id",
            unique=True,
            postgresql_where="resolved_outcome = 'yes'",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    market_group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("market_groups.id"), index=True)
    label: Mapped[str] = mapped_column(String(255))
    # Nullable: most outcomes are "this team wins," but not every outcome has
    # to be a team (e.g. a non-team event market), so this stays optional
    # rather than becoming the required source of truth for the label.
    team_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    status: Mapped[MarketStatus] = mapped_column(Enum(MarketStatus, name="market_status"), default=MarketStatus.open)
    resolved_outcome: Mapped[MarketOutcome | None] = mapped_column(
        Enum(MarketOutcome, name="market_outcome"), nullable=True
    )
    close_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    market_group: Mapped["MarketGroup"] = relationship(back_populates="markets")
