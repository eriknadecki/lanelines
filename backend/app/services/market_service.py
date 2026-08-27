import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Market, MarketGroup, MarketStatus, Team
from app.services.errors import NotFoundError


def create_market_group(
    db: Session,
    *,
    title: str,
    description: str | None,
    team_ids: list[uuid.UUID],
    close_at: datetime | None,
    meet_id: uuid.UUID | None = None,
    meet_event_id: uuid.UUID | None = None,
) -> MarketGroup:
    teams = list(db.execute(select(Team).where(Team.id.in_(team_ids))).scalars().all())
    if len(teams) != len(set(team_ids)):
        raise NotFoundError("one or more teams not found")
    teams_by_id = {team.id: team for team in teams}

    group = MarketGroup(
        title=title, description=description, close_at=close_at, meet_id=meet_id, meet_event_id=meet_event_id
    )
    db.add(group)
    db.flush()

    for team_id in team_ids:
        team = teams_by_id[team_id]
        db.add(
            Market(
                market_group_id=group.id,
                label=f"{team.name} wins",
                team_id=team.id,
                close_at=close_at,
            )
        )

    db.commit()
    db.refresh(group)
    return group


def close_market(db: Session, market_id: uuid.UUID) -> Market:
    market = db.get(Market, market_id)
    if market is None:
        raise NotFoundError("unknown market")
    market.status = MarketStatus.closed
    db.commit()
    db.refresh(market)
    return market
