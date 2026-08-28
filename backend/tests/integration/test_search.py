from app.core.security import create_access_token, hash_password
from app.db.models import Account, AccountOwnerType, User, UserRole


def _make_admin(db_session) -> User:
    admin = User(
        email="searchadmin@example.com",
        username="searchadmin",
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


def test_search_finds_markets_meets_teams_and_swimmers(client, db_session):
    admin = _make_admin(db_session)
    headers = _admin_headers(admin)

    team = client.post(
        "/api/v1/admin/teams", json={"name": "Searchville Sharks", "short_name": "SVS"}, headers=headers
    ).json()
    client.post(
        f"/api/v1/admin/teams/{team['id']}/swimmers", json={"name": "Searchable Swimmer"}, headers=headers
    )
    meet = client.post(
        "/api/v1/admin/meets", json={"name": "Searchville Invitational", "meet_type": "dual"}, headers=headers
    ).json()
    client.post(
        "/api/v1/admin/market-groups",
        json={"title": "Who wins Searchville?", "team_ids": [team["id"]], "meet_id": meet["id"]},
        headers=headers,
    )

    resp = client.get("/api/v1/search", params={"q": "Searchville"})
    assert resp.status_code == 200
    body = resp.json()

    assert any("Searchville" in m["group_title"] for m in body["markets"])
    assert any(m["name"] == "Searchville Invitational" for m in body["meets"])
    assert any(t["name"] == "Searchville Sharks" for t in body["teams"])

    swimmer_resp = client.get("/api/v1/search", params={"q": "Searchable"})
    assert swimmer_resp.status_code == 200
    swimmers = swimmer_resp.json()["swimmers"]
    assert any(s["name"] == "Searchable Swimmer" and s["team_name"] == "Searchville Sharks" for s in swimmers)


def test_search_rejects_short_query(client, db_session):
    resp = client.get("/api/v1/search", params={"q": "a"})
    assert resp.status_code == 422
