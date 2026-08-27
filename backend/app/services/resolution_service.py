import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    LedgerEntryType,
    Market,
    MarketGroup,
    MarketGroupStatus,
    MarketOutcome,
    MarketStatus,
    Position,
)
from app.services import ledger_service
from app.services.account_service import get_user_account
from app.services.errors import AlreadyResolvedError, NotFoundError
from app.services.ledger_service import LedgerEntryInput
from app.services.order_cancellation import cancel_open_orders
from app.ws import events as ws_events
from engine.engine import MatchingEngine


def resolve_market_group(
    db: Session, engine: MatchingEngine, *, group_id: uuid.UUID, winning_market_id: uuid.UUID
) -> MarketGroup:
    group = db.get(MarketGroup, group_id, with_for_update=True)
    if group is None:
        raise NotFoundError("unknown market group")
    if group.status == MarketGroupStatus.resolved:
        raise AlreadyResolvedError("market group is already resolved")

    markets = list(
        db.execute(
            select(Market).where(Market.market_group_id == group_id).with_for_update()
        ).scalars()
    )
    if not any(market.id == winning_market_id for market in markets):
        raise NotFoundError("winning market is not part of this group")

    now = datetime.now(UTC)
    for market in markets:
        cancel_open_orders(db, engine, market)

        market.status = MarketStatus.resolved
        market.resolved_outcome = MarketOutcome.yes if market.id == winning_market_id else MarketOutcome.no
        market.resolved_at = now

        _pay_out_positions(db, market)

    group.status = MarketGroupStatus.resolved
    db.commit()
    db.refresh(group)

    for market in markets:
        ws_events.publish_market_resolved(market.id, group.id, winning_market_id, market.resolved_outcome.value)

    return group


def _pay_out_positions(db: Session, market: Market) -> None:
    escrow = ledger_service.get_market_escrow_account(db, market.id)
    positions = list(
        db.execute(select(Position).where(Position.market_id == market.id).with_for_update()).scalars()
    )
    for position in positions:
        # A resolved-YES market pays 100/contract to net-long-YES holders; a
        # resolved-NO market pays 100/contract to net-long-NO holders (a
        # negative net_yes_quantity). Either way the escrow contribution from
        # every matched trade on this market sums to exactly this payout, by
        # construction of the settlement in order_service.
        payout_quantity = (
            position.net_yes_quantity if market.resolved_outcome == MarketOutcome.yes else -position.net_yes_quantity
        )
        if payout_quantity <= 0:
            continue

        payout_cents = payout_quantity * 100
        account = get_user_account(db, position.user_id)
        ledger_service.post_entry_group(
            db,
            [
                LedgerEntryInput(
                    account_id=escrow.id,
                    entry_type=LedgerEntryType.resolution_payout,
                    amount_cents=-payout_cents,
                    reference_type="market",
                    reference_id=market.id,
                ),
                LedgerEntryInput(
                    account_id=account.id,
                    entry_type=LedgerEntryType.resolution_payout,
                    amount_cents=payout_cents,
                    reference_type="market",
                    reference_id=market.id,
                ),
            ],
        )
