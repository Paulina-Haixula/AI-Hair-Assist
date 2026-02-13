# db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base

# Always use absolute path so Flask & you look at the same file
#BASE_DIR = os.path.abspath(os.path.dirname(__file__))
#DATABASE_PATH = os.path.join(BASE_DIR, "hair_survey.db")
#DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
#DATABASE_URL=mysql+pymysql://root:shalongo@localhost:3306/AI_HAIR_ASSIST
DATABASE_URL = os.getenv('DATABASE_URL')

# Create the engine
engine = create_engine(DATABASE_URL, echo=True, future=True)

# Scoped session for thread-safety in Flask
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

def init_db():
    """Ensure all tables exist."""
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables ensured.")
