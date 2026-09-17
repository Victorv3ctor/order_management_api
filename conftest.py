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

#Fixme 3
# do bazy testowej zrobic Base.create_all na podstawie zmienionych
# modeli (Do Customers dodana hashed_password kolumna) - Pamietac o tym,
# bo teraz mamy rozbieznosc baz pomiedzy produkcyjna a testowa.
# Napewno do poprawy testy ze wzgledu na dodanie kolumny role w customers

load_dotenv()

"""API TESTS"""
# get_db dummy
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
    app.dependency_overrides[get_db] = overrides_db
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


"""UNIT TESTS"""
@pytest.fixture
def payload_items():
    return [
        SimpleNamespace(product_id=1, qty=1),
        SimpleNamespace(product_id=2, qty=1)
    ]

