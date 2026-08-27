import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Market, MarketGroup, MarketGroupStatus, MarketStatus, Order, Team, Trade
from app.services.errors import DeletionBlockedError, NotFoundError
from app.services.order_cancellation import cancel_open_orders
from engine.engine import MatchingEngine


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
