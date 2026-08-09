from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.ingest.pipeline import load_pack, ingest_pack

SAMPLE_PACK_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_challenge_pack.json"


@pytest.fixture()
def db_session():
    """Fresh in-memory SQLite DB per test — fast and fully isolated."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def sample_pack() -> dict:
    return load_pack(SAMPLE_PACK_PATH)


@pytest.fixture()
def seeded_db(db_session, sample_pack):
    """DB session pre-loaded with the synthetic sample challenge pack."""
    ingest_pack(db_session, sample_pack)
    return db_session
