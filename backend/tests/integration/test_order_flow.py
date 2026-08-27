from sqlalchemy import select

from app.config import settings
from app.core.security import create_access_token, hash_password
from app.db.models import Account, AccountOwnerType, User, UserRole
from app.services import auth_service


def _make_admin(db_session) -> User:
    admin = User(
        email="admin@example.com",
        username="admin",
        password_hash=hash_password("adminpass123"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    db_session.flush()
    db_session.add(Account(owner_type=AccountOwnerType.user, owner_id=admin.id))
    db_session.commit()
    return admin


def _admin_headers(admin: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(admin.id)}"}


def _signup(client, db_session, admin: User, email: str, username: str) -> dict:
    invite = auth_service.create_invite(db_session, created_by_user_id=admin.id, max_uses=1, expires_in_days=30)
    resp = client.post(
        "/api/v1/auth/signup",
        json={"invite_code": invite.code, "email": email, "username": username, "password": "password123"},
    )
    assert resp.status_code == 201
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _create_team(client, admin_headers: dict, name: str) -> str:
    resp = client.post(
        "/api/v1/admin/teams",
        json={"name": name, "short_name": name[:20]},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_binary_market(client, admin_headers: dict) -> str:
    team_id = _create_team(client, admin_headers, "Princeton")
    resp = client.post(
        "/api/v1/admin/market-groups",
        json={"title": "Princeton vs Harvard", "team_ids": [team_id]},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    return resp.json()["markets"][0]["id"]


def test_two_opposing_orders_match_via_api(client, db_session):
    admin = _make_admin(db_session)
    admin_headers = _admin_headers(admin)
    alice_headers = _signup(client, db_session, admin, "alice@example.com", "alice")
    bob_headers = _signup(client, db_session, admin, "bob@example.com", "bob")
    market_id = _create_binary_market(client, admin_headers)

    sell_resp = client.post(
        "/api/v1/orders",
        json={
            "market_id": market_id,
            "side": "yes",
            "action": "sell",
            "order_type": "limit",
            "quantity": 10,
            "price_cents": 60,
        },
        headers=bob_headers,
    )
    assert sell_resp.status_code == 201
    assert sell_resp.json()["status"] == "open"

    buy_resp = client.post(
        "/api/v1/orders",
        json={
            "market_id": market_id,
            "side": "yes",
            "action": "buy",
            "order_type": "limit",
            "quantity": 10,
            "price_cents": 60,
        },
        headers=alice_headers,
    )
    assert buy_resp.status_code == 201
    assert buy_resp.json()["status"] == "filled"
    assert buy_resp.json()["filled_quantity"] == 10

    alice_positions = client.get("/api/v1/me/positions", headers=alice_headers).json()
    assert alice_positions == [
        {
            "market_id": market_id,
            "net_yes_quantity": 10,
            "avg_cost_cents": 60,
            "realized_pnl_cents": 0,
        }
    ]

    bob_positions = client.get("/api/v1/me/positions", headers=bob_headers).json()
    assert bob_positions == [
        {
            "market_id": market_id,
            "net_yes_quantity": -10,
            "avg_cost_cents": 60,
            "realized_pnl_cents": 0,
        }
    ]

    # Alice (buyer) pays 60c/contract into escrow; Bob (seller) pays 40c/contract.
    alice_balance = client.get("/api/v1/me/balance", headers=alice_headers).json()
    bob_balance = client.get("/api/v1/me/balance", headers=bob_headers).json()
    assert alice_balance["cash_balance_cents"] == settings.starting_balance_cents - 600
    assert bob_balance["cash_balance_cents"] == settings.starting_balance_cents - 400
    assert alice_balance["held_collateral_cents"] == 0
    assert bob_balance["held_collateral_cents"] == 0

    # Escrow invariant: exactly 100c per matched, unresolved contract.
    escrow = db_session.execute(
        select(Account).where(Account.owner_type == AccountOwnerType.market_escrow)
    ).scalar_one()
    assert escrow.cash_balance_cents == 100 * 10


def test_insufficient_funds_returns_402(client, db_session):
    admin = _make_admin(db_session)
    admin_headers = _admin_headers(admin)
    alice_headers = _signup(client, db_session, admin, "poor@example.com", "poor")
    market_id = _create_binary_market(client, admin_headers)

    resp = client.post(
        "/api/v1/orders",
        json={
            "market_id": market_id,
            "side": "yes",
            "action": "buy",
            "order_type": "limit",
            "quantity": 100_000,
            "price_cents": 99,
        },
        headers=alice_headers,
    )
    assert resp.status_code == 402


def test_order_book_snapshot_reflects_resting_order(client, db_session):
    admin = _make_admin(db_session)
    admin_headers = _admin_headers(admin)
    bob_headers = _signup(client, db_session, admin, "bob2@example.com", "bob2")
    market_id = _create_binary_market(client, admin_headers)

    client.post(
        "/api/v1/orders",
        json={
            "market_id": market_id,
            "side": "yes",
            "action": "buy",
            "order_type": "limit",
            "quantity": 5,
            "price_cents": 42,
        },
        headers=bob_headers,
    )

    book = client.get(f"/api/v1/markets/{market_id}/book").json()
    assert book["bids"] == [{"price_cents": 42, "total_quantity": 5}]
    assert book["asks"] == []


def test_cancel_order_releases_collateral(client, db_session):
    admin = _make_admin(db_session)
    admin_headers = _admin_headers(admin)
    alice_headers = _signup(client, db_session, admin, "alice3@example.com", "alice3")
    market_id = _create_binary_market(client, admin_headers)

    create_resp = client.post(
        "/api/v1/orders",
        json={
            "market_id": market_id,
            "side": "yes",
            "action": "buy",
            "order_type": "limit",
            "quantity": 5,
            "price_cents": 50,
        },
        headers=alice_headers,
    )
    order_id = create_resp.json()["id"]

    balance_after_order = client.get("/api/v1/me/balance", headers=alice_headers).json()
    assert balance_after_order["held_collateral_cents"] == 250  # 50 * 5

    cancel_resp = client.delete(f"/api/v1/orders/{order_id}", headers=alice_headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    balance_after_cancel = client.get("/api/v1/me/balance", headers=alice_headers).json()
    assert balance_after_cancel["held_collateral_cents"] == 0
    assert balance_after_cancel["cash_balance_cents"] == settings.starting_balance_cents
