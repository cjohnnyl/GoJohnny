"""Fixtures globais - Fase 1."""

from __future__ import annotations

import os
import uuid
from typing import Generator

import pytest
import psycopg2
import psycopg2.extensions
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def _ensure_database_url() -> str:
    url = os.getenv("TEST_DATABASE_URL", "")
    if url:
        return url
    try:
        import pgserver  # type: ignore
    except ImportError:
        return ""
    pg_data = "/tmp/pg_data"
    os.makedirs(pg_data, exist_ok=True)
    srv = pgserver.get_server(pg_data, cleanup_mode=None)
    base_uri = srv.get_uri()
    conn = psycopg2.connect(base_uri)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname='gojohnny_test'")
    if cur.fetchone() is None:
        cur.execute("CREATE DATABASE gojohnny_test")
    cur.close()
    conn.close()
    return base_uri.replace("/postgres?", "/gojohnny_test?")


TEST_DATABASE_URL = _ensure_database_url()


@pytest.fixture(scope="session")
def test_engine():
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL indisponivel.")

    engine = create_engine(TEST_DATABASE_URL, future=True)

    from app.core.database import Base
    import app.models.atleta            # noqa: F401
    import app.models.checkin           # noqa: F401
    import app.models.plano_semanal     # noqa: F401
    import app.models.contexto_atleta   # noqa: F401

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    here = os.path.dirname(__file__)
    migrations_dir = os.path.normpath(os.path.join(here, "..", "migrations"))
    if os.path.isdir(migrations_dir):
        for fname in sorted(os.listdir(migrations_dir)):
            if not fname.endswith(".sql"):
                continue
            with open(os.path.join(migrations_dir, fname), "r", encoding="utf-8") as f:
                sql = f.read()
            # psycopg2 puro com autocommit aceita BEGIN/COMMIT como statements
            raw = psycopg2.connect(TEST_DATABASE_URL)
            raw.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            try:
                cur = raw.cursor()
                cur.execute(sql)
                cur.close()
            finally:
                raw.close()

    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    SessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    connection = test_engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def make_apelido():
    def _make(prefix: str = "atleta") -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
    return _make
