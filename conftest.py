import pytest
from main import app
from types import SimpleNamespace
from fastapi.testclient import TestClient
from database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import OrderItem, Order, Customer, Product
import os
from dotenv import load_dotenv


load_dotenv()

"""API TESTS"""
#FUNKCJA ZASTEPUJACA DEPENDS GET_DB -> get_db = overrides_db - polaczenie do testowej
def overrides_db():
    connection_url = os.getenv("DB_TESTS")
    engine = create_engine(connection_url)
    SessionLocal = sessionmaker(bind=engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_db_session():
    connection_url = os.getenv("DB_TESTS")
    engine = create_engine(connection_url)
    return sessionmaker(bind=engine)

#FAST API TESTCLIENT
@pytest.fixture
def client(test_db_session):
    app.dependency_overrides[get_db] = overrides_db  # podmienia globalne Depends = get_db na Depends = overrides_db
    #kazdy endpoint  wykonywany przez client.method, widzi Depends(overrides_db)
    client = TestClient(app)

    yield client

    db = test_db_session()

    db.query(OrderItem).delete()
    db.query(Order).delete()
    db.query(Customer).delete()
    db.query(Product).delete()
    db.commit()
    db.close()

    app.dependency_overrides.clear()
    #czyszczone, bo dla calego procesu pytest, jesli jakis test
    #bedzie chcial dzialac na prawdziwym get_db, czyli nie podmionionym wpisie w
    #slowniku instancji app, to bedzie mogl to zrobic. Inaczej
    #wpis w  slowniku instancji app pozostanie dla calego procesu pytest.


"""UNIT TESTS"""
@pytest.fixture
def payload_items():
    return [
        SimpleNamespace(product_id=1, qty=1),
        SimpleNamespace(product_id=2, qty=1)
    ]

