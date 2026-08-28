from app.core.security import create_access_token, hash_password
from app.db.models import Account, AccountOwnerType, User, UserRole


def _make_admin(db_session) -> User:
    admin = User(
        email="entityadmin@example.com",
        username="entityadmin",
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


def test_create_venue_and_list_it(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)

    resp = client.post(
        "/api/v1/admin/venues",
        json={"name": "DeNunzio Pool", "address": "Princeton, NJ"},
        headers=headers,
    )
    assert resp.status_code == 201
    venue = resp.json()
    assert venue["name"] == "DeNunzio Pool"

    listing = client.get("/api/v1/venues").json()
    assert any(v["id"] == venue["id"] for v in listing)


def test_create_team_with_profile_and_home_venue(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)

    venue = client.post(
        "/api/v1/admin/venues", json={"name": "Blodgett Pool", "address": "Cambridge, MA"}, headers=headers
    ).json()

    resp = client.post(
        "/api/v1/admin/teams",
        json={"name": "Harvard", "short_name": "HARV", "location": "Cambridge, MA", "home_venue_id": venue["id"]},
        headers=headers,
    )
    assert resp.status_code == 201
    team = resp.json()
    assert team["location"] == "Cambridge, MA"
    assert team["home_venue_id"] == venue["id"]

    listing = client.get("/api/v1/teams").json()
    assert any(t["id"] == team["id"] for t in listing)


def test_add_swimmer_to_roster_and_list_it(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)

    team = client.post(
        "/api/v1/admin/teams", json={"name": "Yale", "short_name": "YALE"}, headers=headers
    ).json()

    resp = client.post(
        f"/api/v1/admin/teams/{team['id']}/swimmers",
        json={"name": "Alex Smith", "class_standing": "SR"},
        headers=headers,
    )
    assert resp.status_code == 201
    swimmer = resp.json()
    assert swimmer["team_id"] == team["id"]
    assert swimmer["class_standing"] == "SR"

    roster = client.get(f"/api/v1/teams/{team['id']}/swimmers").json()
    assert [s["name"] for s in roster] == ["Alex Smith"]


def test_create_meet_with_teams_venue_and_tri_type(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)

    home = client.post("/api/v1/admin/teams", json={"name": "Cornell", "short_name": "COR"}, headers=headers).json()
    away = client.post("/api/v1/admin/teams", json={"name": "Columbia", "short_name": "COL"}, headers=headers).json()
    venue = client.post(
        "/api/v1/admin/venues", json={"name": "Teagle Hall", "address": "Ithaca, NY"}, headers=headers
    ).json()

    resp = client.post(
        "/api/v1/admin/meets",
        json={
            "name": "Cornell Tri-Meet",
            "meet_type": "tri",
            "home_team_id": home["id"],
            "away_team_id": away["id"],
            "venue_id": venue["id"],
            "scheduled_at": "2026-11-01T15:00:00Z",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    meet = resp.json()
    assert meet["meet_type"] == "tri"
    assert meet["venue_id"] == venue["id"]
    assert meet["home_team_id"] == home["id"]


def test_market_group_outcomes_are_built_from_teams(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)

    team_a = client.post("/api/v1/admin/teams", json={"name": "Brown", "short_name": "BRWN"}, headers=headers).json()
    team_b = client.post("/api/v1/admin/teams", json={"name": "Dartmouth", "short_name": "DART"}, headers=headers).json()

    resp = client.post(
        "/api/v1/admin/market-groups",
        json={"title": "Who wins?", "team_ids": [team_a["id"], team_b["id"]]},
        headers=headers,
    )
    assert resp.status_code == 201
    markets = resp.json()["markets"]
    labels = {m["label"] for m in markets}
    assert labels == {"Brown wins", "Dartmouth wins"}
    team_ids = {m["team_id"] for m in markets}
    assert team_ids == {team_a["id"], team_b["id"]}


def test_market_group_rejects_unknown_team_id(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)

    resp = client.post(
        "/api/v1/admin/market-groups",
        json={"title": "Bad group", "team_ids": ["00000000-0000-0000-0000-000000000000"]},
        headers=headers,
    )
    assert resp.status_code == 404
