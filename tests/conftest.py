# tests/conftest.py
import os
from collections.abc import Generator
from pathlib import Path

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.db.models import Base

# Always load the project-root .env, regardless of where pytest is run from
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=False)


def _build_sqlalchemy_url(raw_url: str) -> str:
    if raw_url.startswith("postgresql+psycopg://"):
        return raw_url
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw_url


@pytest.fixture(scope="session")
def engine():
    test_db_url = os.getenv("TEST_DATABASE_URL")
    if not test_db_url:
        raise RuntimeError(
            "TEST_DATABASE_URL is not set. Put it in your project .env like:\n"
            "TEST_DATABASE_URL=postgresql://postgres:pass123@127.0.0.1:5433/ecommerce_test"
        )

    engine = create_engine(_build_sqlalchemy_url(test_db_url), pool_pre_ping=True)

    # Fresh schema for tests
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db(engine) -> Generator[Session, None, None]:
    """
    Transactional test pattern:
    - start a transaction
    - run test
    - rollback => DB clean after each test
    """
    connection = engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
