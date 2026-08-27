from app.config import Settings


def test_plain_postgres_url_gets_psycopg_driver() -> None:
    s = Settings(database_url="postgres://user:pw@host:5432/db")
    assert s.database_url == "postgresql+psycopg://user:pw@host:5432/db"


def test_postgresql_url_gets_psycopg_driver() -> None:
    s = Settings(database_url="postgresql://user:pw@host:5432/db")
    assert s.database_url == "postgresql+psycopg://user:pw@host:5432/db"


def test_already_qualified_url_is_left_alone() -> None:
    s = Settings(database_url="postgresql+psycopg://user:pw@host:5432/db")
    assert s.database_url == "postgresql+psycopg://user:pw@host:5432/db"


def test_cors_origins_accepts_comma_separated_string() -> None:
    s = Settings(cors_allow_origins="https://a.example.com, https://b.example.com")
    assert s.cors_allow_origins == ["https://a.example.com", "https://b.example.com"]


def test_cors_origins_accepts_json_array_string() -> None:
    s = Settings(cors_allow_origins='["https://a.example.com","https://b.example.com"]')
    assert s.cors_allow_origins == ["https://a.example.com", "https://b.example.com"]


def test_cors_origins_default() -> None:
    s = Settings()
    assert "http://localhost:5173" in s.cors_allow_origins


def test_cors_origins_comma_separated_via_real_env_var(monkeypatch) -> None:
    # Regression test: pydantic-settings reads env vars through a different
    # code path than direct kwargs (its EnvSettingsSource attempts its own
    # JSON decode for list[str] fields *before* field validators run), and
    # that path crashed the app in production on a plain comma-separated
    # value even though the equivalent direct-kwarg test above passed.
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://a.example.com,https://b.example.com")
    s = Settings()
    assert s.cors_allow_origins == ["https://a.example.com", "https://b.example.com"]


def test_cors_origins_json_array_via_real_env_var(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", '["https://a.example.com","https://b.example.com"]')
    s = Settings()
    assert s.cors_allow_origins == ["https://a.example.com", "https://b.example.com"]
