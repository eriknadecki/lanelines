from app.core.security import create_access_token, hash_password
from app.db.models import Account, AccountOwnerType, User, UserRole
from app.services import auth_service


def _make_admin(db_session) -> User:
    admin = User(
        email="delcsvadmin@example.com",
        username="delcsvadmin",
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


def _create_team(client, headers, name: str, **extra) -> dict:
    resp = client.post("/api/v1/admin/teams", json={"name": name, "short_name": name[:20], **extra}, headers=headers)
    assert resp.status_code == 201
    return resp.json()


def _create_venue(client, headers, name: str) -> dict:
    resp = client.post("/api/v1/admin/venues", json={"name": name}, headers=headers)
    assert resp.status_code == 201
    return resp.json()


def _create_meet(client, headers, name: str, **extra) -> dict:
    resp = client.post("/api/v1/admin/meets", json={"name": name, "meet_type": "dual", **extra}, headers=headers)
    assert resp.status_code == 201
    return resp.json()


def _create_market_group(client, headers, title: str, team_ids: list[str], **extra) -> dict:
    resp = client.post(
        "/api/v1/admin/market-groups", json={"title": title, "team_ids": team_ids, **extra}, headers=headers
    )
    assert resp.status_code == 201
    return resp.json()


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


# --- CSV roster upload ---


def test_upload_roster_csv_happy_path_with_header(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    team = _create_team(client, headers, "CSV Team")

    csv_bytes = b"name,class\nAlex Smith,FR\nJordan Lee,SR\n"
    resp = client.post(
        f"/api/v1/admin/teams/{team['id']}/swimmers/upload-csv",
        files={"file": ("roster.csv", csv_bytes, "text/csv")},
        headers=headers,
    )
    assert resp.status_code == 201
    swimmers = resp.json()
    assert {(s["name"], s["class_standing"]) for s in swimmers} == {("Alex Smith", "FR"), ("Jordan Lee", "SR")}

    roster = client.get(f"/api/v1/teams/{team['id']}/swimmers").json()
    assert {s["name"] for s in roster} == {"Alex Smith", "Jordan Lee"}


def test_upload_roster_csv_no_header_missing_class_and_blank_rows(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    team = _create_team(client, headers, "CSV Team 2")

    csv_bytes = b"Casey Park,\nMorgan Diaz\n\n"
    resp = client.post(
        f"/api/v1/admin/teams/{team['id']}/swimmers/upload-csv",
        files={"file": ("roster.csv", csv_bytes, "text/csv")},
        headers=headers,
    )
    assert resp.status_code == 201
    swimmers = resp.json()
    assert {(s["name"], s["class_standing"]) for s in swimmers} == {
        ("Casey Park", None),
        ("Morgan Diaz", None),
    }


# --- venue deletion ---


def test_delete_venue_success(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    venue = _create_venue(client, headers, "Unused Pool")

    resp = client.delete(f"/api/v1/admin/venues/{venue['id']}", headers=headers)
    assert resp.status_code == 204
    assert all(v["id"] != venue["id"] for v in client.get("/api/v1/venues").json())


def test_delete_venue_blocked_when_home_venue(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    venue = _create_venue(client, headers, "Home Pool")
    _create_team(client, headers, "Homed Team", home_venue_id=venue["id"])

    resp = client.delete(f"/api/v1/admin/venues/{venue['id']}", headers=headers)
    assert resp.status_code == 409


def test_delete_venue_blocked_when_assigned_to_meet(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    venue = _create_venue(client, headers, "Meet Pool")
    _create_meet(client, headers, "Meet At Pool", venue_id=venue["id"])

    resp = client.delete(f"/api/v1/admin/venues/{venue['id']}", headers=headers)
    assert resp.status_code == 409


# --- team deletion ---


def test_delete_team_success_cascades_swimmers(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    team = _create_team(client, headers, "Deletable Team")
    swimmer = client.post(
        f"/api/v1/admin/teams/{team['id']}/swimmers", json={"name": "Solo Swimmer"}, headers=headers
    ).json()
    assert swimmer

    resp = client.delete(f"/api/v1/admin/teams/{team['id']}", headers=headers)
    assert resp.status_code == 204
    assert all(t["id"] != team["id"] for t in client.get("/api/v1/teams").json())


def test_delete_team_blocked_when_market_outcome(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    team = _create_team(client, headers, "Outcome Team")
    _create_market_group(client, headers, "Who wins", [team["id"]])

    resp = client.delete(f"/api/v1/admin/teams/{team['id']}", headers=headers)
    assert resp.status_code == 409


def test_delete_team_blocked_when_assigned_to_meet(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    home = _create_team(client, headers, "Meet Home Team")
    away = _create_team(client, headers, "Meet Away Team")
    _create_meet(client, headers, "Home vs Away", home_team_id=home["id"], away_team_id=away["id"])

    resp = client.delete(f"/api/v1/admin/teams/{home['id']}", headers=headers)
    assert resp.status_code == 409


# --- swimmer deletion ---


def test_delete_swimmer_success(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    team = _create_team(client, headers, "Roster Team")
    swimmer = client.post(
        f"/api/v1/admin/teams/{team['id']}/swimmers", json={"name": "Removable Swimmer"}, headers=headers
    ).json()

    resp = client.delete(f"/api/v1/admin/teams/{team['id']}/swimmers/{swimmer['id']}", headers=headers)
    assert resp.status_code == 204
    roster = client.get(f"/api/v1/teams/{team['id']}/swimmers").json()
    assert all(s["id"] != swimmer["id"] for s in roster)


# --- meet deletion ---


def test_delete_meet_success(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    meet = _create_meet(client, headers, "Deletable Meet")

    resp = client.delete(f"/api/v1/admin/meets/{meet['id']}", headers=headers)
    assert resp.status_code == 204
    assert all(m["id"] != meet["id"] for m in client.get("/api/v1/meets").json())


def test_delete_meet_blocked_when_has_outcomes(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    meet = _create_meet(client, headers, "Meet With Outcome")
    team = _create_team(client, headers, "Outcome Meet Team")
    _create_market_group(client, headers, "Who wins", [team["id"]], meet_id=meet["id"])

    resp = client.delete(f"/api/v1/admin/meets/{meet['id']}", headers=headers)
    assert resp.status_code == 409


# --- meet event deletion ---


def test_delete_meet_event_success(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    meet = _create_meet(client, headers, "Meet With Event")
    event = client.post(
        f"/api/v1/admin/meets/{meet['id']}/events", json={"name": "200 Free", "event_order": 1}, headers=headers
    ).json()

    resp = client.delete(f"/api/v1/admin/meets/{meet['id']}/events/{event['id']}", headers=headers)
    assert resp.status_code == 204
    assert all(e["id"] != event["id"] for e in client.get(f"/api/v1/meets/{meet['id']}/events").json())


def test_delete_meet_event_blocked_when_has_scoped_outcome(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    meet = _create_meet(client, headers, "Meet With Scoped Outcome")
    event = client.post(
        f"/api/v1/admin/meets/{meet['id']}/events", json={"name": "500 Free", "event_order": 1}, headers=headers
    ).json()
    team = _create_team(client, headers, "Event Outcome Team")
    _create_market_group(
        client, headers, "Who wins the event", [team["id"]], meet_id=meet["id"], meet_event_id=event["id"]
    )

    resp = client.delete(f"/api/v1/admin/meets/{meet['id']}/events/{event['id']}", headers=headers)
    assert resp.status_code == 409


def test_delete_meet_event_detaches_ticker_updates(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    meet = _create_meet(client, headers, "Meet With Ticker Event")
    event = client.post(
        f"/api/v1/admin/meets/{meet['id']}/events", json={"name": "100 Fly", "event_order": 1}, headers=headers
    ).json()
    ticker = client.post(
        f"/api/v1/admin/meets/{meet['id']}/ticker",
        json={"body": "Close race", "meet_event_id": event["id"]},
        headers=headers,
    )
    assert ticker.status_code == 201

    resp = client.delete(f"/api/v1/admin/meets/{meet['id']}/events/{event['id']}", headers=headers)
    assert resp.status_code == 204

    feed = client.get(f"/api/v1/meets/{meet['id']}/ticker").json()
    assert feed[0]["meet_event_id"] is None


# --- market group (outcome) deletion ---


def test_delete_market_group_success_releases_collateral(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    alice_headers = _signup(client, db_session, admin, "delalice@example.com", "delalice")
    team = _create_team(client, headers, "Untraded Outcome Team")
    group = _create_market_group(client, headers, "Untraded outcome", [team["id"]])
    market_id = group["markets"][0]["id"]

    resting = _place_order(client, alice_headers, market_id, "buy", 40, 5)
    assert resting["status"] == "open"
    balance_before = client.get("/api/v1/me/balance", headers=alice_headers).json()
    assert balance_before["held_collateral_cents"] == 200  # 40 * 5

    resp = client.delete(f"/api/v1/admin/market-groups/{group['id']}", headers=headers)
    assert resp.status_code == 204

    balance_after = client.get("/api/v1/me/balance", headers=alice_headers).json()
    assert balance_after["held_collateral_cents"] == 0

    listing = client.get("/api/v1/markets").json()
    assert all(g["id"] != group["id"] for g in listing)


def test_delete_market_group_blocked_when_traded(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    alice_headers = _signup(client, db_session, admin, "deltradealice@example.com", "deltradealice")
    bob_headers = _signup(client, db_session, admin, "deltradebob@example.com", "deltradebob")
    team = _create_team(client, headers, "Traded Outcome Team")
    group = _create_market_group(client, headers, "Traded outcome", [team["id"]])
    market_id = group["markets"][0]["id"]

    _place_order(client, bob_headers, market_id, "sell", 50, 5)
    fill = _place_order(client, alice_headers, market_id, "buy", 50, 5)
    assert fill["status"] == "filled"

    resp = client.delete(f"/api/v1/admin/market-groups/{group['id']}", headers=headers)
    assert resp.status_code == 409


def test_delete_market_group_blocked_when_resolved(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)
    team = _create_team(client, headers, "Resolved Outcome Team")
    group = _create_market_group(client, headers, "Resolved outcome", [team["id"]])
    market_id = group["markets"][0]["id"]

    resolve_resp = client.post(
        f"/api/v1/admin/market-groups/{group['id']}/resolve",
        json={"winning_market_id": market_id},
        headers=headers,
    )
    assert resolve_resp.status_code == 200

    resp = client.delete(f"/api/v1/admin/market-groups/{group['id']}", headers=headers)
    assert resp.status_code == 409
