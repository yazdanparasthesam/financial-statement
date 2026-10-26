import pytest

from app.db import make_engine, normalize_database_url


@pytest.mark.unit
@pytest.mark.parametrize(
    ("incoming", "expected"),
    [
        (
            "postgresql://user:pass@ep-example-pooler.eu-central-1.aws.neon.tech/app?sslmode=require",
            "postgresql+psycopg://user:pass@ep-example-pooler.eu-central-1.aws.neon.tech/app?sslmode=require",
        ),
        (
            "postgres://user:pass@db.example/app?sslmode=require",
            "postgresql+psycopg://user:pass@db.example/app?sslmode=require",
        ),
        ("postgresql+psycopg://user:pass@db.example/app", "postgresql+psycopg://user:pass@db.example/app"),
        ("sqlite:///./local.db", "sqlite:///./local.db"),
    ],
)
def test_database_url_uses_psycopg3_without_losing_connection_options(incoming, expected):
    assert normalize_database_url(incoming) == expected


@pytest.mark.unit
def test_make_engine_uses_psycopg3_for_neon_url():
    engine = make_engine(
        "postgresql://user:pass@ep-example-pooler.eu-central-1.aws.neon.tech/app?sslmode=require"
    )
    try:
        assert engine.url.drivername == "postgresql+psycopg"
        assert engine.url.host == "ep-example-pooler.eu-central-1.aws.neon.tech"
        assert engine.url.query["sslmode"] == "require"
    finally:
        engine.dispose()
