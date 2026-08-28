from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import Market, MarketGroup, Meet, Swimmer, Team
from app.db.session import get_db
from app.schemas.search import (
    MarketSearchResult,
    MeetSearchResult,
    SearchResultsOut,
    SwimmerSearchResult,
    TeamSearchResult,
)

router = APIRouter(tags=["search"])

RESULT_LIMIT = 6


@router.get("/search", response_model=SearchResultsOut)
def search(q: str = Query(min_length=2), db: Session = Depends(get_db)) -> SearchResultsOut:
    like = f"%{q}%"

    markets = list(
        db.execute(
            select(Market, MarketGroup.title)
            .join(MarketGroup, Market.market_group_id == MarketGroup.id)
            .where(or_(Market.label.ilike(like), MarketGroup.title.ilike(like)))
            .limit(RESULT_LIMIT)
        ).all()
    )
    meets = list(db.execute(select(Meet).where(Meet.name.ilike(like)).limit(RESULT_LIMIT)).scalars().all())
    teams = list(db.execute(select(Team).where(Team.name.ilike(like)).limit(RESULT_LIMIT)).scalars().all())
    swimmers = list(
        db.execute(
            select(Swimmer, Team.name)
            .join(Team, Swimmer.team_id == Team.id)
            .where(Swimmer.name.ilike(like))
            .limit(RESULT_LIMIT)
        ).all()
    )

    return SearchResultsOut(
        markets=[
            MarketSearchResult(id=m.id, label=m.label, group_title=title, status=m.status) for m, title in markets
        ],
        meets=[MeetSearchResult(id=m.id, name=m.name, meet_type=m.meet_type) for m in meets],
        teams=[TeamSearchResult(id=t.id, name=t.name, short_name=t.short_name) for t in teams],
        swimmers=[SwimmerSearchResult(id=s.id, name=s.name, team_name=team_name) for s, team_name in swimmers],
    )
