from sqlalchemy import text

from app.config import settings
from app.core.security import hash_password
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


def _make_invite(db_session, max_uses: int = 1):
    admin = _make_admin(db_session)
    return auth_service.create_invite(
        db_session, created_by_user_id=admin.id, max_uses=max_uses, expires_in_days=30
    )


def test_signup_via_invite_grants_starting_balance(client, db_session):
    invite = _make_invite(db_session)

    resp = client.post(
        "/api/v1/auth/signup",
        json={
            "invite_code": invite.code,
            "email": "friend@example.com",
            "username": "friend1",
            "password": "supersecret1",
        },
    )
    assert resp.status_code == 201
    tokens = resp.json()
    assert "access_token" in tokens

    balance_resp = client.get(
        "/api/v1/me/balance", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert balance_resp.status_code == 200
    body = balance_resp.json()
    assert body["cash_balance_cents"] == settings.starting_balance_cents
    assert body["available_cents"] == settings.starting_balance_cents


def test_invite_cannot_be_reused_past_max_uses(client, db_session):
    invite = _make_invite(db_session, max_uses=1)

    first = client.post(
        "/api/v1/auth/signup",
        json={"invite_code": invite.code, "email": "a@example.com", "username": "usera", "password": "password123"},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/auth/signup",
        json={"invite_code": invite.code, "email": "b@example.com", "username": "userb", "password": "password123"},
    )
    assert second.status_code == 400


def test_login_with_correct_and_incorrect_password(client, db_session):
    invite = _make_invite(db_session)
    client.post(
        "/api/v1/auth/signup",
        json={
            "invite_code": invite.code,
            "email": "login@example.com",
            "username": "loginuser",
            "password": "correcthorse",
        },
    )

    good = client.post("/api/v1/auth/login", json={"email": "login@example.com", "password": "correcthorse"})
    assert good.status_code == 200
    assert "access_token" in good.json()

    bad = client.post("/api/v1/auth/login", json={"email": "login@example.com", "password": "wrongpass"})
    assert bad.status_code == 401


def test_change_password_with_correct_current_password(client, db_session):
    invite = _make_invite(db_session)
    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "invite_code": invite.code,
            "email": "changepw@example.com",
            "username": "changepwuser",
            "password": "originalpass1",
        },
    )
    access_token = signup.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = client.post(
        "/api/v1/me/password",
        headers=headers,
        json={"current_password": "originalpass1", "new_password": "newpassword2"},
    )
    assert resp.status_code == 204

    old_login = client.post(
        "/api/v1/auth/login", json={"email": "changepw@example.com", "password": "originalpass1"}
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login", json={"email": "changepw@example.com", "password": "newpassword2"}
    )
    assert new_login.status_code == 200


def test_change_password_rejects_wrong_current_password(client, db_session):
    invite = _make_invite(db_session)
    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "invite_code": invite.code,
            "email": "wrongcurrent@example.com",
            "username": "wrongcurrentuser",
            "password": "originalpass1",
        },
    )
    access_token = signup.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = client.post(
        "/api/v1/me/password",
        headers=headers,
        json={"current_password": "notmypassword", "new_password": "newpassword2"},
    )
    assert resp.status_code == 401

    still_works = client.post(
        "/api/v1/auth/login", json={"email": "wrongcurrent@example.com", "password": "originalpass1"}
    )
    assert still_works.status_code == 200


def test_ledger_group_sums_to_zero_after_signup(client, db_session):
    invite = _make_invite(db_session)
    client.post(
        "/api/v1/auth/signup",
        json={
            "invite_code": invite.code,
            "email": "ledger@example.com",
            "username": "ledgeruser",
            "password": "password123",
        },
    )

    total = db_session.execute(text("SELECT SUM(amount_cents) FROM ledger_entries")).scalar_one()
    assert total == 0
