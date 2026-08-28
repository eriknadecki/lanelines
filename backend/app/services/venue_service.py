import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Meet, Team, Venue
from app.services.errors import AlreadyExistsError, DeletionBlockedError, NotFoundError


def create_venue(db: Session, *, name: str, address: str | None) -> Venue:
    existing = db.execute(select(Venue.id).where(Venue.name == name)).scalar_one_or_none()
    if existing is not None:
        raise AlreadyExistsError("A venue with that name already exists")

    venue = Venue(name=name, address=address)
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return venue


def list_venues(db: Session) -> list[Venue]:
    return list(db.execute(select(Venue).order_by(Venue.name)).scalars().all())


def delete_venue(db: Session, venue_id: uuid.UUID) -> None:
    venue = db.get(Venue, venue_id)
    if venue is None:
        raise NotFoundError("unknown venue")

    referenced_by_team = db.execute(
        select(Team.id).where(Team.home_venue_id == venue_id).limit(1)
    ).scalar_one_or_none()
    if referenced_by_team is not None:
        raise DeletionBlockedError("cannot delete a venue that's a team's home venue")

    referenced_by_meet = db.execute(
        select(Meet.id).where(Meet.venue_id == venue_id).limit(1)
    ).scalar_one_or_none()
    if referenced_by_meet is not None:
        raise DeletionBlockedError("cannot delete a venue that's assigned to a meet")

    db.delete(venue)
    db.commit()
