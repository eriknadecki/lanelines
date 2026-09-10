import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import hash_password, verify_password
from app.db.models import Account, AccountOwnerType, Invite, LedgerEntryType, User
from app.services import ledger_service
from app.services.errors import InvalidCredentialsError, InviteInvalidError, UserAlreadyExistsError
from app.services.ledger_service import LedgerEntryInput


def _get_valid_invite(db: Session, code: str) -> Invite:
    invite = db.execute(
        select(Invite).where(Invite.code == code).with_for_update()
    ).scalar_one_or_none()
    if invite is None:
        raise InviteInvalidError("Invite code not found")
    if invite.expires_at is not None and invite.expires_at < datetime.now(UTC):
        raise InviteInvalidError("Invite code has expired")
    if invite.uses_count >= invite.max_uses:
        raise InviteInvalidError("Invite code has already been used")
    return invite


def check_invite(db: Session, code: str) -> str | None:
    """Returns None if the invite is usable, else a reason it isn't."""
    try:
        _get_valid_invite(db, code)
    except InviteInvalidError as exc:
        return str(exc)
    return None


def create_invite(db: Session, created_by_user_id: uuid.UUID, max_uses: int, expires_in_days: int | None) -> Invite:
    expires_at = (
        datetime.now(UTC) + timedelta(days=expires_in_days) if expires_in_days else None
    )
    invite = Invite(
        code=secrets.token_urlsafe(8),
        created_by_user_id=created_by_user_id,
        max_uses=max_uses,
        expires_at=expires_at,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


def signup(db: Session, invite_code: str, email: str, username: str, password: str) -> User:
    invite = _get_valid_invite(db, invite_code)

    existing = db.execute(
        select(User).where((User.email == email) | (User.username == username))
    ).scalar_one_or_none()
    if existing is not None:
        raise UserAlreadyExistsError("Email or username already in use")

    user = User(email=email, username=username, password_hash=hash_password(password))
    db.add(user)
    db.flush()

    account = Account(owner_type=AccountOwnerType.user, owner_id=user.id, cash_balance_cents=0)
    db.add(account)
    db.flush()

    invite.uses_count += 1

    house_account = ledger_service.get_house_account(db)
    ledger_service.post_entry_group(
        db,
        [
            LedgerEntryInput(
                account_id=house_account.id,
                entry_type=LedgerEntryType.initial_grant,
                amount_cents=-settings.starting_balance_cents,
                reference_type="invite",
                reference_id=invite.id,
            ),
            LedgerEntryInput(
                account_id=account.id,
                entry_type=LedgerEntryType.initial_grant,
                amount_cents=settings.starting_balance_cents,
                reference_type="invite",
                reference_id=invite.id,
            ),
        ],
    )

    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("Invalid email or password")
    return user


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise InvalidCredentialsError("Current password is incorrect")
    user.password_hash = hash_password(new_password)
    db.commit()
