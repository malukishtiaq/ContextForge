from contextlib import contextmanager
from sqlmodel import SQLModel, Session, create_engine

from app.core.config import settings

engine = create_engine(f"sqlite:///{settings.sqlite_path}", echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Session:
    with Session(engine) as session:
        yield session

