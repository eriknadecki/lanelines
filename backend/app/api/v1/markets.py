import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_engine
from app.db.models import Market, MarketGroup, TeamConference, TeamDivision
from app.db.session import get_db
from app.schemas.market import (
    BookSnapshotOut,
    MarketCategory,
    MarketGroupOut,
    MarketOut,
    PriceLevelOut,
)
from app.services import market_service
from engine.engine import MatchingEngine

router = APIRouter(prefix="/markets", tags=["markets"])


@router.get("", response_model=list[MarketGroupOut])
def list_market_groups(
    category: MarketCategory | None = Query(None),
    division: TeamDivision | None = Query(None),
    conference: TeamConference | None = Query(None),
    db: Session = Depends(get_db),
) -> list[MarketGroup]:
    return market_service.list_market_groups(db, category=category, division=division, conference=conference)


@router.get("/{market_id}", response_model=MarketOut)
def get_market(market_id: uuid.UUID, db: Session = Depends(get_db)) -> Market:
    market = db.get(Market, market_id)
    if market is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="market not found")
    return market


@router.get("/{market_id}/book", response_model=BookSnapshotOut)
def get_market_book(
    market_id: uuid.UUID,
    depth: int = 10,
    db: Session = Depends(get_db),
    engine: MatchingEngine = Depends(get_engine),
) -> BookSnapshotOut:
    market = db.get(Market, market_id)
    if market is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="market not found")

    snapshot = engine.get_book_snapshot(str(market_id), depth=depth)
    return BookSnapshotOut(
        market_id=market_id,
        bids=[PriceLevelOut(price_cents=p.price_cents, total_quantity=p.total_quantity) for p in snapshot.bids],
        asks=[PriceLevelOut(price_cents=p.price_cents, total_quantity=p.total_quantity) for p in snapshot.asks],
    )
