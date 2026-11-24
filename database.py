import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("Set DATABASE_URL to the SkillSwap PostgreSQL connection URL.")

engine = create_engine(database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
