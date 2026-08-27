"""Bootstrap an admin user and an invite to send to friends.

Idempotent: if the email already exists, it promotes that user to admin
and resets their password to the one given, rather than silently leaving
their role untouched (re-running this used to be a no-op on role, which
was confusing — "I ran it again and it's still not admin").

Usage:
    python scripts/create_admin.py you@example.com yourname yourpassword
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import Account, AccountOwnerType, User, UserRole
from app.db.session import SessionLocal
from app.services import auth_service


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email")
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("--invite-max-uses", type=int, default=20)
    parser.add_argument("--invite-expires-days", type=int, default=90)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        existing = db.execute(select(User).where(User.email == args.email)).scalar_one_or_none()
        if existing is not None:
            was_admin = existing.role == UserRole.admin
            existing.role = UserRole.admin
            existing.password_hash = hash_password(args.password)
            db.commit()
            db.refresh(existing)
            admin = existing
            if was_admin:
                print(f"'{admin.email}' was already admin (id={admin.id}); password reset.")
            else:
                print(f"Promoted existing user '{admin.email}' (id={admin.id}) to admin; password reset.")
        else:
            admin = User(
                email=args.email,
                username=args.username,
                password_hash=hash_password(args.password),
                role=UserRole.admin,
            )
            db.add(admin)
            db.flush()
            db.add(Account(owner_type=AccountOwnerType.user, owner_id=admin.id))
            db.commit()
            db.refresh(admin)
            print(f"Created admin user '{admin.email}' (id={admin.id}).")

        invite = auth_service.create_invite(
            db,
            created_by_user_id=admin.id,
            max_uses=args.invite_max_uses,
            expires_in_days=args.invite_expires_days,
        )
        print(f"Invite code: {invite.code}")
        print(f"Share signup with this code (max_uses={invite.max_uses}, expires_at={invite.expires_at}).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
