from app.core.security import create_access_token, hash_password
from app.db.models import Account, AccountOwnerType, Meet, MeetStatus, User, UserRole
from app.services import auth_service


def _make_admin(db_session) -> User:
    admin = User(
        email="marketsadmin@example.com",
        username="marketsadmin",
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


def _create_team(client, headers: dict, name: str, *, division: str | None = None, conference: str | None = None) -> str:
    payload = {"name": name, "short_name": name[:20]}
    if division is not None:
        payload["division"] = division
    if conference is not None:
        payload["conference"] = conference
    resp = client.post("/api/v1/admin/teams", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_meet(client, headers: dict, name: str, meet_type: str, **kwargs) -> str:
    resp = client.post(
        "/api/v1/admin/meets", json={"name": name, "meet_type": meet_type, **kwargs}, headers=headers
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_market_group(client, headers: dict, title: str, team_id: str, **kwargs) -> str:
    resp = client.post(
        "/api/v1/admin/market-groups",
        json={"title": title, "team_ids": [team_id], **kwargs},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def test_category_filters_by_meet_type(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    team = _create_team(client, headers, "Type Filter Team")

    dual_meet = _create_meet(client, headers, "Dual Meet", "dual")
    invite_meet = _create_meet(client, headers, "Invite Meet", "invite")
    champ_meet = _create_meet(client, headers, "Champ Meet", "championship")

    dual_group = _create_market_group(client, headers, "Dual Group", team, meet_id=dual_meet)
    invite_group = _create_market_group(client, headers, "Invite Group", team, meet_id=invite_meet)
    champ_group = _create_market_group(client, headers, "Champ Group", team, meet_id=champ_meet)

    dual_tri_ids = {g["id"] for g in client.get("/api/v1/markets", params={"category": "dual_tri"}).json()}
    assert dual_group in dual_tri_ids
    assert invite_group not in dual_tri_ids
    assert champ_group not in dual_tri_ids

    invite_ids = {g["id"] for g in client.get("/api/v1/markets", params={"category": "invite"}).json()}
    assert invite_ids == {invite_group}

    champ_ids = {g["id"] for g in client.get("/api/v1/markets", params={"category": "championship"}).json()}
    assert champ_ids == {champ_group}


def test_category_event_result_filters_by_meet_event(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    team = _create_team(client, headers, "Event Result Team")
    meet = _create_meet(client, headers, "Event Meet", "dual")
    event_resp = client.post(
        "/api/v1/admin/meets/" + meet + "/events", json={"name": "200 Free", "event_order": 1}, headers=headers
    )
    assert event_resp.status_code == 201
    event_id = event_resp.json()["id"]

    whole_meet_group = _create_market_group(client, headers, "Whole Meet Group", team, meet_id=meet)
    event_group = _create_market_group(
        client, headers, "Event Group", team, meet_id=meet, meet_event_id=event_id
    )

    ids = {g["id"] for g in client.get("/api/v1/markets", params={"category": "event_result"}).json()}
    assert ids == {event_group}
    assert whole_meet_group not in ids


def test_category_live_filters_by_meet_status(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    team = _create_team(client, headers, "Live Filter Team")
    live_meet_id = _create_meet(client, headers, "Live Meet", "dual")
    scheduled_meet_id = _create_meet(client, headers, "Scheduled Meet", "dual")

    live_meet = db_session.get(Meet, live_meet_id)
    live_meet.status = MeetStatus.live
    db_session.commit()

    live_group = _create_market_group(client, headers, "Live Group", team, meet_id=live_meet_id)
    scheduled_group = _create_market_group(client, headers, "Scheduled Group", team, meet_id=scheduled_meet_id)

    ids = {g["id"] for g in client.get("/api/v1/markets", params={"category": "live"}).json()}
    assert ids == {live_group}
    assert scheduled_group not in ids


def test_division_and_conference_filters(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    d1_team = _create_team(
        client, headers, "D1 ACC Team", division="D1", conference="Atlantic Coast Conference"
    )
    d3_team = _create_team(
        client, headers, "D3 NESCAC Team", division="D3", conference="New England Small College Athletic Conference"
    )

    d1_meet = _create_meet(client, headers, "D1 Meet", "dual", home_team_id=d1_team)
    d3_meet = _create_meet(client, headers, "D3 Meet", "dual", home_team_id=d3_team)

    d1_group = _create_market_group(client, headers, "D1 Group", d1_team, meet_id=d1_meet)
    d3_group = _create_market_group(client, headers, "D3 Group", d3_team, meet_id=d3_meet)

    d1_ids = {g["id"] for g in client.get("/api/v1/markets", params={"division": "D1"}).json()}
    assert d1_ids == {d1_group}

    acc_ids = {
        g["id"]
        for g in client.get("/api/v1/markets", params={"conference": "Atlantic Coast Conference"}).json()
    }
    assert acc_ids == {d1_group}
    assert d3_group not in acc_ids


def test_trending_orders_by_trade_activity(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)

    invite = auth_service.create_invite(db_session, created_by_user_id=admin.id, max_uses=1, expires_in_days=30)
    alice = client.post(
        "/api/v1/auth/signup",
        json={"invite_code": invite.code, "email": "trendalice@example.com", "username": "trendalice", "password": "password123"},
    ).json()
    invite2 = auth_service.create_invite(db_session, created_by_user_id=admin.id, max_uses=1, expires_in_days=30)
    bob = client.post(
        "/api/v1/auth/signup",
        json={"invite_code": invite2.code, "email": "trendbob@example.com", "username": "trendbob", "password": "password123"},
    ).json()
    alice_headers = {"Authorization": f"Bearer {alice['access_token']}"}
    bob_headers = {"Authorization": f"Bearer {bob['access_token']}"}

    quiet_team = _create_team(client, headers, "Quiet Team")
    active_team = _create_team(client, headers, "Active Team")
    quiet_group = _create_market_group(client, headers, "Quiet Group", quiet_team)
    active_group = _create_market_group(client, headers, "Active Group", active_team)

    all_groups = client.get("/api/v1/markets").json()
    active_market_id = next(g for g in all_groups if g["id"] == active_group)["markets"][0]["id"]

    client.post(
        "/api/v1/orders",
        json={"market_id": active_market_id, "side": "yes", "action": "sell", "order_type": "limit", "quantity": 5, "price_cents": 50},
        headers=bob_headers,
    )
    client.post(
        "/api/v1/orders",
        json={"market_id": active_market_id, "side": "yes", "action": "buy", "order_type": "limit", "quantity": 5, "price_cents": 50},
        headers=alice_headers,
    )

    trending = client.get("/api/v1/markets", params={"category": "trending"}).json()
    trending_ids = [g["id"] for g in trending]
    assert trending_ids.index(active_group) < trending_ids.index(quiet_group)
