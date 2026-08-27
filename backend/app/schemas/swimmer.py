import uuid

from pydantic import BaseModel, Field


class CreateSwimmerRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    class_year: int | None = None


class SwimmerOut(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    name: str
    class_year: int | None

    model_config = {"from_attributes": True}
