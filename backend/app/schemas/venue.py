import uuid

from pydantic import BaseModel, Field

from app.db.models import CourseType


class CreateVenueRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str | None = None
    course_type: CourseType | None = None


class VenueOut(BaseModel):
    id: uuid.UUID
    name: str
    address: str | None
    course_type: CourseType | None

    model_config = {"from_attributes": True}
