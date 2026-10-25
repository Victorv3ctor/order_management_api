from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.exceptions import DatabaseError
import os
from dotenv import load_dotenv
load_dotenv()

connection_url = os.getenv("DATABASE_URL")
engine = create_engine(connection_url, hide_parameters=True)
SessionLocal = sessionmaker(bind=engine, autoflush=True)

def database_health_check(db):
    try:
        db.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as error:
        raise DatabaseError from error

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()




























