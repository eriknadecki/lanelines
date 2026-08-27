from fastapi.testclient import TestClient

from app.core.deps import get_engine
from app.core.security import create_access_token, hash_password
from app.db.models import Account, AccountOwnerType, User, UserRole
from app.db.session import get_db
from app.main import app
from app.services import auth_service


def _make_admin(db_session) -> User:
    admin = User(
        email="wsadmin@example.com",
        username="wsadmin",
        password_hash=hash_password("adminpass123"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    db_session.flush()
    db_session.add(Account(owner_type=AccountOwnerType.user, owner_id=admin.id))
    db_session.commit()
    return admin


def test_book_update_and_trade_broadcast_over_websocket(db_session, matching_engine):
    admin = _make_admin(db_session)
    invite = auth_service.create_invite(db_session, created_by_user_id=admin.id, max_uses=2, expires_in_days=30)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_engine] = lambda: matching_engine

    try:
        # Must enter as a context manager so FastAPI's lifespan actually runs
        # and binds the WS manager to a real event loop — a bare TestClient(app)
        # (as used elsewhere) never fires lifespan, so broadcast() is a no-op.
        with TestClient(app) as client:
            admin_headers = {"Authorization": f"Bearer {create_access_token(admin.id)}"}
            team_resp = client.post(
                "/api/v1/admin/teams",
                json={"name": "WS Team", "short_name": "WST"},
                headers=admin_headers,
            )
            team_id = team_resp.json()["id"]
            group_resp = client.post(
                "/api/v1/admin/market-groups",
                json={"title": "WS Test", "team_ids": [team_id]},
                headers=admin_headers,
            )
            market_id = group_resp.json()["markets"][0]["id"]

            alice_resp = client.post(
                "/api/v1/auth/signup",
                json={
                    "invite_code": invite.code,
                    "email": "wsalice@example.com",
                    "username": "wsalice",
                    "password": "password123",
                },
            )
            bob_resp = client.post(
                "/api/v1/auth/signup",
                json={
                    "invite_code": invite.code,
                    "email": "wsbob@example.com",
                    "username": "wsbob",
                    "password": "password123",
                },
            )
            alice_token = alice_resp.json()["access_token"]
            alice_headers = {"Authorization": f"Bearer {alice_token}"}
            bob_headers = {"Authorization": f"Bearer {bob_resp.json()['access_token']}"}

            with client.websocket_connect(f"/ws?token={alice_token}") as ws:
                ws.send_json({"type": "subscribe", "channel": f"market:{market_id}"})

                # Bob rests a sell order on a market Alice is watching but
                # hasn't traded on — she should see exactly one book_update,
                # nothing from Bob's own private channel.
                client.post(
                    "/api/v1/orders",
                    json={
                        "market_id": market_id,
                        "side": "yes",
                        "action": "sell",
                        "order_type": "limit",
                        "quantity": 10,
                        "price_cents": 55,
                    },
                    headers=bob_headers,
                )
                resting_book_msg = ws.receive_json()
                assert resting_book_msg == {
                    "type": "book_update",
                    "market_id": market_id,
                    "bids": [],
                    "asks": [{"price_cents": 55, "total_quantity": 10}],
                    "sequence": 1,
                }

                # Alice crosses it. Her socket is subscribed to both the
                # market channel and (automatically) her own private channel,
                # so she should see 4 messages: her own order_update and
                # balance_update, the trade, and the post-trade book_update.
                # Bob's private order_update/balance_update do not appear
                # here since Alice never subscribed to his channel.
                client.post(
                    "/api/v1/orders",
                    json={
                        "market_id": market_id,
                        "side": "yes",
                        "action": "buy",
                        "order_type": "limit",
                        "quantity": 10,
                        "price_cents": 55,
                    },
                    headers=alice_headers,
                )
                messages = [ws.receive_json() for _ in range(4)]
                by_type = {msg["type"]: msg for msg in messages}
                assert set(by_type) == {"order_update", "balance_update", "trade", "book_update"}

                assert by_type["trade"]["price_cents"] == 55
                assert by_type["trade"]["quantity"] == 10
                assert by_type["trade"]["market_id"] == market_id

                assert by_type["book_update"]["bids"] == []
                assert by_type["book_update"]["asks"] == []

                assert by_type["order_update"]["status"] == "filled"
                assert by_type["order_update"]["filled_quantity"] == 10

                assert by_type["balance_update"]["cash_balance_cents"] == 1_000_000 - 550
    finally:
        app.dependency_overrides.clear()
