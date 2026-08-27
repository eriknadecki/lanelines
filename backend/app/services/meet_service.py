import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Meet, MeetEvent, MeetType, Team


def create_team(
    db: Session,
    *,
    name: str,
    short_name: str,
    location: str | None,
    home_venue_id: uuid.UUID | None,
) -> Team:
    team = Team(name=name, short_name=short_name, location=location, home_venue_id=home_venue_id)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


def create_meet(
    db: Session,
    *,
    name: str,
    meet_type: MeetType,
    home_team_id: uuid.UUID | None,
    away_team_id: uuid.UUID | None,
    scheduled_at: datetime | None,
    venue_id: uuid.UUID | None,
) -> Meet:
    meet = Meet(
        name=name,
        meet_type=meet_type,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        scheduled_at=scheduled_at,
        venue_id=venue_id,
    )
    db.add(meet)
    db.commit()
    db.refresh(meet)
    return meet


def create_meet_event(
    db: Session, *, meet_id: uuid.UUID, name: str, event_order: int, scheduled_at: datetime | None
) -> MeetEvent:
    event = MeetEvent(meet_id=meet_id, name=name, event_order=event_order, scheduled_at=scheduled_at)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
