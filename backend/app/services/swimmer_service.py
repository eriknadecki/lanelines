import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Swimmer


def create_swimmer(db: Session, *, team_id: uuid.UUID, name: str, class_year: int | None) -> Swimmer:
    swimmer = Swimmer(team_id=team_id, name=name, class_year=class_year)
    db.add(swimmer)
    db.commit()
    db.refresh(swimmer)
    return swimmer


def list_swimmers(db: Session, *, team_id: uuid.UUID | None = None) -> list[Swimmer]:
    query = select(Swimmer).order_by(Swimmer.name)
    if team_id is not None:
        query = query.where(Swimmer.team_id == team_id)
    return list(db.execute(query).scalars().all())
