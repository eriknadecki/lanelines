from sqlalchemy import select

from app.core.security import create_access_token, hash_password
from app.db.models import Account, AccountOwnerType, User, UserRole
from app.services import auth_service


def _make_admin(db_session) -> User:
    admin = User(
        email="resadmin@example.com",
        username="resadmin",
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


def _place_order(client, headers, market_id, action, price_cents, quantity):
    resp = client.post(
        "/api/v1/orders",
        json={
            "market_id": market_id,
            "side": "yes",
            "action": action,
            "order_type": "limit",
            "quantity": quantity,
            "price_cents": price_cents,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


def test_full_lifecycle_trade_ticker_resolve_payout(client, db_session):
    admin = _make_admin(db_session)
    admin_headers = _admin_headers(admin)
    alice_headers = _signup(client, db_session, admin, "resalice@example.com", "resalice")
    bob_headers = _signup(client, db_session, admin, "resbob@example.com", "resbob")

    meet_resp = client.post(
        "/api/v1/admin/meets",
        json={"name": "Princeton vs Harvard", "meet_type": "dual"},
        headers=admin_headers,
    )
    assert meet_resp.status_code == 201
    meet_id = meet_resp.json()["id"]

    princeton_id = _create_team(client, admin_headers, "Princeton")
    group_resp = client.post(
        "/api/v1/admin/market-groups",
        json={"title": "Who wins the meet?", "team_ids": [princeton_id], "meet_id": meet_id},
        headers=admin_headers,
    )
    assert group_resp.status_code == 201
    group_id = group_resp.json()["id"]
    market_id = group_resp.json()["markets"][0]["id"]

    # Trade: Bob sells 10 YES @ 60, Alice buys 10 YES @ 60 — fully matched.
    _place_order(client, bob_headers, market_id, "sell", 60, 10)
    fill = _place_order(client, alice_headers, market_id, "buy", 60, 10)
    assert fill["status"] == "filled"

    # A ticker update is posted — it must have zero effect on the market.
    book_before = client.get(f"/api/v1/markets/{market_id}/book").json()
    ticker_resp = client.post(
        f"/api/v1/admin/meets/{meet_id}/ticker",
        json={"body": "Princeton wins the 200 Free Relay"},
        headers=admin_headers,
    )
    assert ticker_resp.status_code == 201
    book_after = client.get(f"/api/v1/markets/{market_id}/book").json()
    assert book_before == book_after

    feed = client.get(f"/api/v1/meets/{meet_id}/ticker").json()
    assert len(feed) == 1
    assert feed[0]["body"] == "Princeton wins the 200 Free Relay"

    # Bob rests another order after the trade — resolution must cancel it
    # and release its collateral, not just settle already-matched positions.
    bob_resting = _place_order(client, bob_headers, market_id, "sell", 70, 5)
    assert bob_resting["status"] == "open"
    bob_balance_pre_resolve = client.get("/api/v1/me/balance", headers=bob_headers).json()
    assert bob_balance_pre_resolve["held_collateral_cents"] == 150  # (100-70)*5

    resolve_resp = client.post(
        f"/api/v1/admin/market-groups/{group_id}/resolve",
        json={"winning_market_id": market_id},
        headers=admin_headers,
    )
    assert resolve_resp.status_code == 200
    resolved_market = resolve_resp.json()["markets"][0]
    assert resolved_market["status"] == "resolved"
    assert resolved_market["resolved_outcome"] == "yes"

    bob_order_after = client.get("/api/v1/orders", params={"market_id": market_id}, headers=bob_headers).json()
    resting_order_after = next(o for o in bob_order_after if o["id"] == bob_resting["id"])
    assert resting_order_after["status"] == "cancelled"

    alice_balance = client.get("/api/v1/me/balance", headers=alice_headers).json()
    bob_balance = client.get("/api/v1/me/balance", headers=bob_headers).json()
    assert alice_balance["cash_balance_cents"] == 1_000_000 - 600 + 1000  # paid 600, won 1000
    assert alice_balance["held_collateral_cents"] == 0
    assert bob_balance["cash_balance_cents"] == 1_000_000 - 400  # paid 400, won nothing
    assert bob_balance["held_collateral_cents"] == 0  # the cancelled resting order's hold was released

    escrow = db_session.execute(
        select(Account).where(Account.owner_type == AccountOwnerType.market_escrow)
    ).scalar_one()
    assert escrow.cash_balance_cents == 0  # fully paid out


def test_resolving_twice_is_rejected(client, db_session):
    admin = _make_admin(db_session)
    admin_headers = _admin_headers(admin)
    team_a = _create_team(client, admin_headers, "Team A")
    team_b = _create_team(client, admin_headers, "Team B")
    group_resp = client.post(
        "/api/v1/admin/market-groups",
        json={"title": "Test group", "team_ids": [team_a, team_b]},
        headers=admin_headers,
    )
    group_id = group_resp.json()["id"]
    market_id = group_resp.json()["markets"][0]["id"]

    first = client.post(
        f"/api/v1/admin/market-groups/{group_id}/resolve",
        json={"winning_market_id": market_id},
        headers=admin_headers,
    )
    assert first.status_code == 200

    second = client.post(
        f"/api/v1/admin/market-groups/{group_id}/resolve",
        json={"winning_market_id": market_id},
        headers=admin_headers,
    )
    assert second.status_code == 409


def test_closed_market_rejects_new_orders(client, db_session):
    admin = _make_admin(db_session)
    admin_headers = _admin_headers(admin)
    alice_headers = _signup(client, db_session, admin, "resalice2@example.com", "resalice2")

    team_id = _create_team(client, admin_headers, "Closeable Team")
    group_resp = client.post(
        "/api/v1/admin/market-groups",
        json={"title": "Closeable", "team_ids": [team_id]},
        headers=admin_headers,
    )
    market_id = group_resp.json()["markets"][0]["id"]

    close_resp = client.post(f"/api/v1/admin/markets/{market_id}/close", headers=admin_headers)
    assert close_resp.status_code == 200
    assert close_resp.json()["status"] == "closed"

    order_resp = client.post(
        "/api/v1/orders",
        json={
            "market_id": market_id,
            "side": "yes",
            "action": "buy",
            "order_type": "limit",
            "quantity": 1,
            "price_cents": 50,
        },
        headers=alice_headers,
    )
    assert order_resp.status_code == 409
