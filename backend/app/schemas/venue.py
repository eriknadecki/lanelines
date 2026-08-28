import uuid

from pydantic import BaseModel, Field


class CreateVenueRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str | None = None


class VenueOut(BaseModel):
    id: uuid.UUID
    name: str
    address: str | None

    model_config = {"from_attributes": True}
