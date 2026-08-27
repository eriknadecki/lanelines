import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.market import MarketGroupStatus, MarketOutcome, MarketStatus


class CreateMarketGroupRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    team_ids: list[uuid.UUID] = Field(min_length=1, max_length=32)
    close_at: datetime | None = None
    meet_id: uuid.UUID | None = None
    meet_event_id: uuid.UUID | None = None


class ResolveMarketGroupRequest(BaseModel):
    winning_market_id: uuid.UUID


class MarketOut(BaseModel):
    id: uuid.UUID
    label: str
    team_id: uuid.UUID | None
    status: MarketStatus
    resolved_outcome: MarketOutcome | None

    model_config = {"from_attributes": True}


class MarketGroupOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    status: MarketGroupStatus
    close_at: datetime | None
    meet_id: uuid.UUID | None
    meet_event_id: uuid.UUID | None
    markets: list[MarketOut]

    model_config = {"from_attributes": True}


class PriceLevelOut(BaseModel):
    price_cents: int
    total_quantity: int


class BookSnapshotOut(BaseModel):
    market_id: uuid.UUID
    bids: list[PriceLevelOut]
    asks: list[PriceLevelOut]
