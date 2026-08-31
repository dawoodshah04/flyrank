"""Database connection for Python AI services.

Uses SQLAlchemy for direct table access to the same PostgreSQL DB
that Prisma manages on the TypeScript side.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ai.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def get_session():
    """Get a new database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_db():
    """Get a direct database session (non-generator)."""
    return SessionLocal()
