import csv
import io
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Swimmer
from app.services.errors import NotFoundError


def create_swimmer(db: Session, *, team_id: uuid.UUID, name: str, class_standing: str | None) -> Swimmer:
    swimmer = Swimmer(team_id=team_id, name=name, class_standing=class_standing)
    db.add(swimmer)
    db.commit()
    db.refresh(swimmer)
    return swimmer


def list_swimmers(db: Session, *, team_id: uuid.UUID | None = None) -> list[Swimmer]:
    query = select(Swimmer).order_by(Swimmer.name)
    if team_id is not None:
        query = query.where(Swimmer.team_id == team_id)
    return list(db.execute(query).scalars().all())


def bulk_create_swimmers_from_csv(db: Session, *, team_id: uuid.UUID, csv_bytes: bytes) -> list[Swimmer]:
    """Column 1: name, column 2: class standing (FR/SO/JR/SR/etc, optional).
    A header row is tolerated (and skipped) but not required."""
    text = csv_bytes.decode("utf-8-sig")
    rows = [row for row in csv.reader(io.StringIO(text)) if any(cell.strip() for cell in row)]

    if rows and rows[0][0].strip().lower() in ("name", "athlete", "swimmer"):
        rows = rows[1:]

    swimmers = []
    for row in rows:
        name = row[0].strip()
        if not name:
            continue
        class_standing = row[1].strip() if len(row) > 1 and row[1].strip() else None
        swimmers.append(Swimmer(team_id=team_id, name=name, class_standing=class_standing))

    db.add_all(swimmers)
    db.commit()
    for swimmer in swimmers:
        db.refresh(swimmer)
    return swimmers


def delete_swimmer(db: Session, swimmer_id: uuid.UUID) -> None:
    swimmer = db.get(Swimmer, swimmer_id)
    if swimmer is None:
        raise NotFoundError("unknown swimmer")
    db.delete(swimmer)
    db.commit()
