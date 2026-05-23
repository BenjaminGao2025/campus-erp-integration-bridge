from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


engine = None
SessionLocal: sessionmaker[Session] | None = None


def configure_database(database_url: str | None = None) -> None:
    global engine, SessionLocal
    url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


def get_session() -> Generator[Session, None, None]:
    if SessionLocal is None:
        configure_database()
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database() -> None:
    if engine is None:
        configure_database()
    from app import models  # noqa: F401

    assert engine is not None
    Base.metadata.create_all(bind=engine)


def reset_database() -> None:
    if engine is None:
        configure_database()
    from app import models  # noqa: F401

    assert engine is not None
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
