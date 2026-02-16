from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from maspatas.infrastructure.db.models import Base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://maspatas:maspatas@localhost:5432/maspatas",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
