from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CourseType, Venue


def create_venue(db: Session, *, name: str, address: str | None, course_type: CourseType | None) -> Venue:
    venue = Venue(name=name, address=address, course_type=course_type)
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return venue


def list_venues(db: Session) -> list[Venue]:
    return list(db.execute(select(Venue).order_by(Venue.name)).scalars().all())
