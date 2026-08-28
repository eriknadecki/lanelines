import uuid
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import Market, MarketGroup, Meet, MeetEvent, MeetType, Team, TickerUpdate
from app.services.errors import AlreadyExistsError, DeletionBlockedError, NotFoundError


def create_team(
    db: Session,
    *,
    name: str,
    short_name: str,
    location: str | None,
    home_venue_id: uuid.UUID | None,
) -> Team:
    existing = db.execute(select(Team.id).where(Team.name == name)).scalar_one_or_none()
    if existing is not None:
        raise AlreadyExistsError("A team with that name already exists")

    team = Team(name=name, short_name=short_name, location=location, home_venue_id=home_venue_id)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


def delete_team(db: Session, team_id: uuid.UUID) -> None:
    team = db.get(Team, team_id)
    if team is None:
        raise NotFoundError("unknown team")

    referenced_by_market = db.execute(select(Market.id).where(Market.team_id == team_id).limit(1)).scalar_one_or_none()
    if referenced_by_market is not None:
        raise DeletionBlockedError("cannot delete a team that's already an outcome on a market")

    referenced_by_meet = db.execute(
        select(Meet.id).where(or_(Meet.home_team_id == team_id, Meet.away_team_id == team_id)).limit(1)
    ).scalar_one_or_none()
    if referenced_by_meet is not None:
        raise DeletionBlockedError("cannot delete a team that's assigned to a meet — remove it from the meet first")

    db.delete(team)  # roster (swimmers) cascades at the DB level
    db.commit()


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


def delete_meet(db: Session, meet_id: uuid.UUID) -> None:
    meet = db.get(Meet, meet_id)
    if meet is None:
        raise NotFoundError("unknown meet")

    has_outcomes = db.execute(
        select(MarketGroup.id).where(MarketGroup.meet_id == meet_id).limit(1)
    ).scalar_one_or_none()
    if has_outcomes is not None:
        raise DeletionBlockedError("cannot delete a meet with outcomes on it — delete those first")

    # Ticker updates and events are pure information with no trading
    # activity of their own, so they're safe to cascade automatically.
    db.execute(TickerUpdate.__table__.delete().where(TickerUpdate.meet_id == meet_id))
    db.execute(MeetEvent.__table__.delete().where(MeetEvent.meet_id == meet_id))
    db.delete(meet)
    db.commit()


def create_meet_event(
    db: Session, *, meet_id: uuid.UUID, name: str, event_order: int, scheduled_at: datetime | None
) -> MeetEvent:
    event = MeetEvent(meet_id=meet_id, name=name, event_order=event_order, scheduled_at=scheduled_at)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def delete_meet_event(db: Session, event_id: uuid.UUID) -> None:
    event = db.get(MeetEvent, event_id)
    if event is None:
        raise NotFoundError("unknown meet event")

    has_outcomes = db.execute(
        select(MarketGroup.id).where(MarketGroup.meet_event_id == event_id).limit(1)
    ).scalar_one_or_none()
    if has_outcomes is not None:
        raise DeletionBlockedError("cannot delete an event with outcomes scoped to it — delete those first")

    # Detach (not delete) any ticker posts that referenced this event —
    # they're still valid meet-level history, just no longer event-scoped.
    db.execute(
        TickerUpdate.__table__.update().where(TickerUpdate.meet_event_id == event_id).values(meet_event_id=None)
    )
    db.delete(event)
    db.commit()
