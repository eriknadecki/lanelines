import uuid

from pydantic import BaseModel, Field


class CreateTeamRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    short_name: str = Field(min_length=1, max_length=20)
    location: str | None = None
    home_venue_id: uuid.UUID | None = None


class TeamOut(BaseModel):
    id: uuid.UUID
    name: str
    short_name: str
    location: str | None
    home_venue_id: uuid.UUID | None

    model_config = {"from_attributes": True}
