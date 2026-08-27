import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.core.deps import get_engine
from app.db import models  # noqa: F401  (registers tables on Base.metadata)
from app.db.session import Base, get_db
from app.main import app
from engine.engine import MatchingEngine

_TEST_DATABASE_URL = settings.database_url.rsplit("/", 1)[0] + "/lanelines_test"
_TABLES_IN_FK_ORDER = [
    "trades",
    "orders",
    "positions",
    "ledger_entries",
    "markets",
    "market_groups",
    "ticker_updates",
    "meet_events",
    "meets",
    "swimmers",
    "teams",
    "venues",
    "invites",
    "accounts",
    "users",
]


def _recreate_test_database() -> None:
    # Drop and recreate the whole database on every run so the test schema
    # can never drift from the models — create_all() alone only ever adds
    # missing tables, so a column/constraint removed in code but left behind
    # from a prior run (as happened here once already) would otherwise
    # silently persist and produce confusing failures.
    admin_engine = create_engine(settings.database_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = 'lanelines_test' AND pid != pg_backend_pid()"
            )
        )
        conn.execute(text("DROP DATABASE IF EXISTS lanelines_test"))
        conn.execute(text("CREATE DATABASE lanelines_test"))
    admin_engine.dispose()


_recreate_test_database()
_test_db_engine = create_engine(_TEST_DATABASE_URL)
Base.metadata.create_all(_test_db_engine)
TestSessionLocal = sessionmaker(bind=_test_db_engine, autoflush=False, autocommit=False)


@pytest.fixture()
def db_session():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        for table in _TABLES_IN_FK_ORDER:
            session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        session.commit()
        session.close()


@pytest.fixture()
def matching_engine():
    # A fresh in-memory engine per test — the app's real engine is a
    # process-wide singleton, which would otherwise leak resting orders
    # between test cases.
    return MatchingEngine()


@pytest.fixture()
def client(db_session, matching_engine):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_engine] = lambda: matching_engine
    yield TestClient(app)
    app.dependency_overrides.clear()
