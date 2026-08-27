import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Meet, MeetEvent, Swimmer, Team, TickerUpdate, Venue
from app.db.session import get_db
from app.schemas.meet import MeetEventOut, MeetOut, TickerUpdateOut
from app.schemas.swimmer import SwimmerOut
from app.schemas.team import TeamOut
from app.schemas.venue import VenueOut
from app.services import swimmer_service, venue_service

router = APIRouter(tags=["meets"])


@router.get("/venues", response_model=list[VenueOut])
def list_venues(db: Session = Depends(get_db)) -> list[Venue]:
    return venue_service.list_venues(db)


@router.get("/teams", response_model=list[TeamOut])
def list_teams(db: Session = Depends(get_db)) -> list[Team]:
    return list(db.execute(select(Team)).scalars().all())


@router.get("/teams/{team_id}/swimmers", response_model=list[SwimmerOut])
def list_swimmers(team_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Swimmer]:
    return swimmer_service.list_swimmers(db, team_id=team_id)


@router.get("/meets", response_model=list[MeetOut])
def list_meets(db: Session = Depends(get_db)) -> list[Meet]:
    return list(db.execute(select(Meet).order_by(Meet.scheduled_at)).scalars().all())


@router.get("/meets/{meet_id}", response_model=MeetOut)
def get_meet(meet_id: uuid.UUID, db: Session = Depends(get_db)) -> Meet:
    meet = db.get(Meet, meet_id)
    if meet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="meet not found")
    return meet


@router.get("/meets/{meet_id}/events", response_model=list[MeetEventOut])
def list_meet_events(meet_id: uuid.UUID, db: Session = Depends(get_db)) -> list[MeetEvent]:
    return list(
        db.execute(
            select(MeetEvent).where(MeetEvent.meet_id == meet_id).order_by(MeetEvent.event_order)
        ).scalars().all()
    )


@router.get("/meets/{meet_id}/ticker", response_model=list[TickerUpdateOut])
def get_meet_ticker(meet_id: uuid.UUID, db: Session = Depends(get_db)) -> list[TickerUpdate]:
    return list(
        db.execute(
            select(TickerUpdate).where(TickerUpdate.meet_id == meet_id).order_by(TickerUpdate.created_at)
        ).scalars().all()
    )
