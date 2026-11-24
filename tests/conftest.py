import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.schema import CreateSchema, DropSchema


@pytest.fixture
def db_engine():
    test_url = os.getenv("TEST_DATABASE_URL")
    if not test_url:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        try:
            with engine.connect() as connection:
                connection.exec_driver_sql("PRAGMA foreign_keys = ON")
            yield engine
        finally:
            engine.dispose()
        return

    url = make_url(test_url)
    if url.get_backend_name() != "postgresql":
        raise pytest.UsageError("TEST_DATABASE_URL must point to a PostgreSQL test database.")

    engine = create_engine(url)
    schema = f"skillswap_test_{uuid4().hex}"
    try:
        with engine.begin() as connection:
            connection.execute(CreateSchema(schema))
        try:
            yield engine.execution_options(schema_translate_map={None: schema})
        finally:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
    finally:
        engine.dispose()


@pytest.fixture
def client(db_engine, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("JWT_SECRET_KEY", "skillswap-test-signing-key")
    from database import Base, get_db
    from main import app

    Base.metadata.create_all(bind=db_engine)

    def get_test_db():
        with Session(bind=db_engine, autoflush=False) as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, get_test_db)
    with TestClient(app) as test_client:
        yield test_client
