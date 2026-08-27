import uuid

from pydantic import BaseModel, Field


class CreateSwimmerRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    class_standing: str | None = Field(default=None, max_length=10)


class SwimmerOut(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    name: str
    class_standing: str | None

    model_config = {"from_attributes": True}
