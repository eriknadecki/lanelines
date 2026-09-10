from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.models import Account, AccountOwnerType, Position, User
from app.db.session import get_db
from app.schemas.account import BalanceOut
from app.schemas.auth import ChangePasswordRequest, UserOut
from app.schemas.order import PositionOut
from app.services import auth_service
from app.services.errors import InvalidCredentialsError

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        auth_service.change_password(db, user, payload.current_password, payload.new_password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get("/balance", response_model=BalanceOut)
def get_balance(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> BalanceOut:
    account = db.execute(
        select(Account).where(
            Account.owner_type == AccountOwnerType.user, Account.owner_id == user.id
        )
    ).scalar_one()
    return BalanceOut(
        cash_balance_cents=account.cash_balance_cents,
        held_collateral_cents=account.held_collateral_cents,
        available_cents=account.cash_balance_cents - account.held_collateral_cents,
    )


@router.get("/positions", response_model=list[PositionOut])
def get_positions(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Position]:
    return list(
        db.execute(select(Position).where(Position.user_id == user.id)).scalars().all()
    )
