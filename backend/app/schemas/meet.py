import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.meet import MeetEventStatus, MeetStatus, MeetType


class CreateMeetRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    meet_type: MeetType
    home_team_id: uuid.UUID | None = None
    away_team_id: uuid.UUID | None = None
    scheduled_at: datetime | None = None
    venue_id: uuid.UUID | None = None


class MeetOut(BaseModel):
    id: uuid.UUID
    name: str
    meet_type: MeetType
    home_team_id: uuid.UUID | None
    away_team_id: uuid.UUID | None
    scheduled_at: datetime | None
    status: MeetStatus
    venue_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class CreateMeetEventRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    event_order: int = 0
    scheduled_at: datetime | None = None


class MeetEventOut(BaseModel):
    id: uuid.UUID
    meet_id: uuid.UUID
    name: str
    event_order: int
    status: MeetEventStatus
    scheduled_at: datetime | None

    model_config = {"from_attributes": True}


class CreateTickerUpdateRequest(BaseModel):
    meet_event_id: uuid.UUID | None = None
    body: str = Field(min_length=1, max_length=2000)


class TickerUpdateOut(BaseModel):
    id: uuid.UUID
    meet_id: uuid.UUID
    meet_event_id: uuid.UUID | None
    author_id: uuid.UUID
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}
