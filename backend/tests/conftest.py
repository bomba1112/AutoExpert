from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from app import models  # noqa: F401
from app.core.config import get_settings
from app.db.base import Base
from app.db.ordering import add_row_order
from app.db.session import get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(autouse=True)
def secure_feature_flags_for_tests() -> Generator[None, None, None]:
    """Keep the existing production-security baseline unless a test opts into dev mode."""

    settings = get_settings()
    original_developer_mode = settings.developer_mode
    original_simulation = settings.developer_simulate_user_paywall_default
    original_subscription = settings.subscription_v1
    settings.developer_mode = False
    settings.developer_simulate_user_paywall_default = False
    # subscription rights (stage 6) are tested in test_subscription.py; other tests see every right
    settings.subscription_v1 = False
    try:
        yield
    finally:
        settings.developer_mode = original_developer_mode
        settings.developer_simulate_user_paywall_default = original_simulation
        settings.subscription_v1 = original_subscription


# AUTOEXPERT_TEST_DATABASE_URL=postgresql+psycopg://... runs the tests on PostgreSQL (deploy
# prompt, stage A): the schema is created once, every test runs in a transaction rolled back at
# the end (the application's commits become savepoints). Unset: in-memory SQLite per test.
TEST_DATABASE_URL = os.environ.get("AUTOEXPERT_TEST_DATABASE_URL")


@pytest.fixture(scope="session")
def postgres_engine():
    if not TEST_DATABASE_URL:
        yield None
        return
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        add_row_order(connection)  # as migration f095 does on PostgreSQL
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(postgres_engine) -> Generator[Session, None, None]:
    if postgres_engine is not None:
        connection = postgres_engine.connect()
        outer = connection.begin()
        session = Session(bind=connection, autoflush=False, expire_on_commit=False,
                          join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            outer.rollback()
            connection.close()
        return
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with testing_session() as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
