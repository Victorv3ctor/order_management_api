from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
load_dotenv()

#Do polaczenia uzyj zmienna srodowiskowa DATABASE_URL (ta zmienna srodowiskowa tworzy services
#app (kontener api przy starcie kontenera), jesli jej nie ma (dzialam lokalnie), uzyj zmiennej
#srodowiskowej DB_LOCALHOST z dotenv
connection_url = os.environ.get(
    "DATABASE_URL",
    os.environ.get("DB_LOCALHOST")
)


engine = create_engine(connection_url, echo=True)

SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()






















