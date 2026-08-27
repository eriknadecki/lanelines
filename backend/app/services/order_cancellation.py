from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Market, Order
from app.services.account_service import get_user_account
from engine.engine import MatchingEngine
from engine.types import OrderStatus


def cancel_open_orders(db: Session, engine: MatchingEngine, market: Market) -> None:
    """Cancel every still-open/partially-filled order on a market, releasing
    each owner's held collateral. Shared by resolution (a market's outcome is
    now known, nothing more can trade) and admin deletion (undoing a setup
    mistake before any real trading happened)."""
    open_orders = list(
        db.execute(
            select(Order)
            .where(Order.market_id == market.id, Order.status.in_([OrderStatus.open, OrderStatus.partially_filled]))
            .with_for_update()
        ).scalars()
    )
    for order in open_orders:
        result = engine.cancel_order(str(market.id), order.id)
        if result.status == OrderStatus.cancelled:
            account = get_user_account(db, order.user_id)
            account.held_collateral_cents -= order.collateral_cents
            order.collateral_cents = 0
            order.status = OrderStatus.cancelled
