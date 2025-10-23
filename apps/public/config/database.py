"""
Database configuration for public website.

Uses PostgreSQL for central system data (landing pages, analytics).
Separate from user databases which use Turso.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env.public if it exists
env_path = Path(__file__).parent.parent.parent.parent / ".env.public"
if env_path.exists():
    load_dotenv(env_path)


def get_database_url() -> str:
    """
    Get PostgreSQL database URL.

    Returns connection string for central PostgreSQL database.
    """
    url = os.getenv(
        "PUBLIC_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/multicardz_public"
    )
    return url


def get_db():
    """
    Get database session (generator for FastAPI Depends).

    Yields SQLAlchemy session for request handling.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(get_database_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
