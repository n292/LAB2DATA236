from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

# Lab 2: Migrated to MongoDB. This file is kept as a dummy for legacy imports.
# Using SQLite as a safe fallback that doesn't require a server and won't crash on import.
import pathlib
db_path = pathlib.Path(__file__).parent.parent / "yelp_legacy_dummy.db"
DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
