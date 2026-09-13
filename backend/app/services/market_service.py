import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased

from app.db.models import (
    Market,
    MarketGroup,
    MarketGroupStatus,
    MarketStatus,
    Meet,
    MeetStatus,
    MeetType,
    Order,
    Team,
    TeamConference,
    TeamDivision,
    Trade,
)
from app.schemas.market import MarketCategory
from app.services.errors import DeletionBlockedError, NotFoundError
from app.services.order_cancellation import cancel_open_orders
from engine.engine import MatchingEngine

_MEET_TYPE_CATEGORIES = {
    MarketCategory.dual_tri: (MeetType.dual, MeetType.tri),
    MarketCategory.invite: (MeetType.invite,),
    MarketCategory.championship: (MeetType.championship,),
}


def list_market_groups(
    db: Session,
    *,
    category: MarketCategory | None = None,
    division: TeamDivision | None = None,
    conference: TeamConference | None = None,
) -> list[MarketGroup]:
    query = select(MarketGroup)

    needs_meet_join = (
        category in (MarketCategory.live, *_MEET_TYPE_CATEGORIES) or division is not None or conference is not None
    )
    if needs_meet_join:
        query = query.join(Meet, MarketGroup.meet_id == Meet.id)

    if category == MarketCategory.event_result:
        query = query.where(MarketGroup.meet_event_id.is_not(None))
    elif category == MarketCategory.live:
        query = query.where(Meet.status == MeetStatus.live)
    elif category in _MEET_TYPE_CATEGORIES:
        query = query.where(Meet.meet_type.in_(_MEET_TYPE_CATEGORIES[category]))

    if division is not None or conference is not None:
        home_team = aliased(Team)
        away_team = aliased(Team)
        query = query.outerjoin(home_team, Meet.home_team_id == home_team.id).outerjoin(
            away_team, Meet.away_team_id == away_team.id
        )
        if division is not None:
            query = query.where(or_(home_team.division == division, away_team.division == division))
        if conference is not None:
            query = query.where(or_(home_team.conference == conference, away_team.conference == conference))

    if category == MarketCategory.trending:
        trade_counts = (
            select(Market.market_group_id.label("market_group_id"), func.count(Trade.id).label("trade_count"))
            .outerjoin(Trade, Trade.market_id == Market.id)
            .group_by(Market.market_group_id)
            .subquery()
        )
        query = query.outerjoin(trade_counts, trade_counts.c.market_group_id == MarketGroup.id)
        query = query.order_by(trade_counts.c.trade_count.desc().nulls_last(), MarketGroup.created_at.desc())
    else:
        query = query.order_by(MarketGroup.created_at.desc())

    return list(db.execute(query).scalars().all())


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


def delete_market_group(db: Session, engine: MatchingEngine, group_id: uuid.UUID) -> None:
    group = db.get(MarketGroup, group_id, with_for_update=True)
    if group is None:
        raise NotFoundError("unknown market group")
    if group.status == MarketGroupStatus.resolved:
        raise DeletionBlockedError("cannot delete a resolved outcome — its payouts have already been sent")

    markets = list(
        db.execute(select(Market).where(Market.market_group_id == group_id).with_for_update()).scalars()
    )
    market_ids = [market.id for market in markets]
    if market_ids:
        trade_count = db.execute(select(func.count()).select_from(Trade).where(Trade.market_id.in_(market_ids))).scalar_one()
        if trade_count > 0:
            raise DeletionBlockedError("cannot delete an outcome that already has trades — resolve it instead")

    for market in markets:
        cancel_open_orders(db, engine, market)
        # Flush the cancellations before the raw DELETE below, or the ORM's
        # pending UPDATEs for these orders would target rows that no longer
        # exist and raise a StaleDataError at commit.
        db.flush()
        # Zero trades means every order on this market is either cancelled
        # or was never matched, so it's safe to purge — nothing real is lost.
        db.execute(Order.__table__.delete().where(Order.market_id == market.id))
        db.delete(market)
    db.delete(group)
    db.commit()
