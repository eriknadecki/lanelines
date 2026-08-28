import uuid

from pydantic import BaseModel

from app.db.models.market import MarketStatus
from app.db.models.meet import MeetType


class MarketSearchResult(BaseModel):
    id: uuid.UUID
    label: str
    group_title: str
    status: MarketStatus


class MeetSearchResult(BaseModel):
    id: uuid.UUID
    name: str
    meet_type: MeetType


class TeamSearchResult(BaseModel):
    id: uuid.UUID
    name: str
    short_name: str


class SwimmerSearchResult(BaseModel):
    id: uuid.UUID
    name: str
    team_name: str


class SearchResultsOut(BaseModel):
    markets: list[MarketSearchResult]
    meets: list[MeetSearchResult]
    teams: list[TeamSearchResult]
    swimmers: list[SwimmerSearchResult]
