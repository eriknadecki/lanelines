import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_engine, require_admin
from app.db.models import (
    Market,
    MarketGroup,
    Meet,
    MeetEvent,
    Swimmer,
    Team,
    TickerUpdate,
    User,
    Venue,
)
from app.db.session import get_db
from app.schemas.invite import CreateInviteRequest, InviteOut
from app.schemas.market import (
    CreateMarketGroupRequest,
    MarketGroupOut,
    MarketOut,
    ResolveMarketGroupRequest,
)
from app.schemas.meet import (
    CreateMeetEventRequest,
    CreateMeetRequest,
    CreateTickerUpdateRequest,
    MeetEventOut,
    MeetOut,
    TickerUpdateOut,
)
from app.schemas.swimmer import CreateSwimmerRequest, SwimmerOut
from app.schemas.team import CreateTeamRequest, TeamOut
from app.schemas.venue import CreateVenueRequest, VenueOut
from app.services import (
    auth_service,
    market_service,
    meet_service,
    resolution_service,
    swimmer_service,
    ticker_service,
    venue_service,
)
from app.services.errors import (
    AlreadyResolvedError,
    DeletionBlockedError,
    NotFoundError,
    ServiceError,
)
from engine.engine import MatchingEngine

router = APIRouter(prefix="/admin", tags=["admin"])


def _to_http_error(exc: ServiceError) -> HTTPException:
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, (DeletionBlockedError, AlreadyResolvedError)):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/invites", response_model=InviteOut)
def create_invite(
    payload: CreateInviteRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> InviteOut:
    invite = auth_service.create_invite(
        db,
        created_by_user_id=admin.id,
        max_uses=payload.max_uses,
        expires_in_days=payload.expires_in_days,
    )
    return InviteOut(
        code=invite.code,
        max_uses=invite.max_uses,
        uses_count=invite.uses_count,
        expires_at=invite.expires_at,
    )


@router.post("/venues", response_model=VenueOut, status_code=status.HTTP_201_CREATED)
def create_venue(
    payload: CreateVenueRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Venue:
    return venue_service.create_venue(db, name=payload.name, address=payload.address)


@router.delete("/venues/{venue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_venue(
    venue_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> None:
    try:
        venue_service.delete_venue(db, venue_id)
    except ServiceError as exc:
        raise _to_http_error(exc) from exc


@router.post("/teams", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: CreateTeamRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Team:
    return meet_service.create_team(
        db,
        name=payload.name,
        short_name=payload.short_name,
        location=payload.location,
        home_venue_id=payload.home_venue_id,
    )


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> None:
    try:
        meet_service.delete_team(db, team_id)
    except ServiceError as exc:
        raise _to_http_error(exc) from exc


@router.post("/teams/{team_id}/swimmers", response_model=SwimmerOut, status_code=status.HTTP_201_CREATED)
def create_swimmer(
    team_id: uuid.UUID,
    payload: CreateSwimmerRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Swimmer:
    return swimmer_service.create_swimmer(
        db, team_id=team_id, name=payload.name, class_standing=payload.class_standing
    )


@router.post(
    "/teams/{team_id}/swimmers/upload-csv", response_model=list[SwimmerOut], status_code=status.HTTP_201_CREATED
)
async def upload_roster_csv(
    team_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> list[Swimmer]:
    csv_bytes = await file.read()
    return swimmer_service.bulk_create_swimmers_from_csv(db, team_id=team_id, csv_bytes=csv_bytes)


@router.delete("/teams/{team_id}/swimmers/{swimmer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_swimmer(
    team_id: uuid.UUID,
    swimmer_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> None:
    try:
        swimmer_service.delete_swimmer(db, swimmer_id)
    except ServiceError as exc:
        raise _to_http_error(exc) from exc


@router.post("/meets", response_model=MeetOut, status_code=status.HTTP_201_CREATED)
def create_meet(
    payload: CreateMeetRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Meet:
    return meet_service.create_meet(
        db,
        name=payload.name,
        meet_type=payload.meet_type,
        home_team_id=payload.home_team_id,
        away_team_id=payload.away_team_id,
        scheduled_at=payload.scheduled_at,
        venue_id=payload.venue_id,
    )


@router.delete("/meets/{meet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meet(
    meet_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> None:
    try:
        meet_service.delete_meet(db, meet_id)
    except ServiceError as exc:
        raise _to_http_error(exc) from exc


@router.post("/meets/{meet_id}/events", response_model=MeetEventOut, status_code=status.HTTP_201_CREATED)
def create_meet_event(
    meet_id: uuid.UUID,
    payload: CreateMeetEventRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> MeetEvent:
    return meet_service.create_meet_event(
        db,
        meet_id=meet_id,
        name=payload.name,
        event_order=payload.event_order,
        scheduled_at=payload.scheduled_at,
    )


@router.delete("/meets/{meet_id}/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meet_event(
    meet_id: uuid.UUID,
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> None:
    try:
        meet_service.delete_meet_event(db, event_id)
    except ServiceError as exc:
        raise _to_http_error(exc) from exc


@router.post("/meets/{meet_id}/ticker", response_model=TickerUpdateOut, status_code=status.HTTP_201_CREATED)
def post_ticker_update(
    meet_id: uuid.UUID,
    payload: CreateTickerUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> TickerUpdate:
    return ticker_service.post_ticker_update(
        db, meet_id=meet_id, meet_event_id=payload.meet_event_id, author_id=admin.id, body=payload.body
    )


@router.post("/market-groups", response_model=MarketGroupOut, status_code=status.HTTP_201_CREATED)
def create_market_group(
    payload: CreateMarketGroupRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> MarketGroup:
    try:
        return market_service.create_market_group(
            db,
            title=payload.title,
            description=payload.description,
            team_ids=payload.team_ids,
            close_at=payload.close_at,
            meet_id=payload.meet_id,
            meet_event_id=payload.meet_event_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/market-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_market_group(
    group_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    engine: MatchingEngine = Depends(get_engine),
) -> None:
    try:
        market_service.delete_market_group(db, engine, group_id)
    except ServiceError as exc:
        raise _to_http_error(exc) from exc


@router.post("/markets/{market_id}/close", response_model=MarketOut)
def close_market(
    market_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Market:
    try:
        return market_service.close_market(db, market_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/market-groups/{group_id}/resolve", response_model=MarketGroupOut)
def resolve_market_group(
    group_id: uuid.UUID,
    payload: ResolveMarketGroupRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    engine: MatchingEngine = Depends(get_engine),
) -> MarketGroup:
    try:
        return resolution_service.resolve_market_group(
            db, engine, group_id=group_id, winning_market_id=payload.winning_market_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AlreadyResolvedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
