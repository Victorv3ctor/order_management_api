import pytest
from api.main import app
from types import SimpleNamespace
from fastapi.testclient import TestClient
from database import get_db
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Customer, Product
from security import create_token
import os
from dotenv import load_dotenv
load_dotenv()
import sys
print(sys.path)


"get_db DUMMY"
def overrides_db():
    connection_url = os.getenv("DB_TESTS")
    engine = create_engine(connection_url, echo=True)

    SessionLocal = sessionmaker(bind=engine)

    db = SessionLocal()
    try:
        print('yielded')
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        print('closed')
        db.close()

def customer_auth_token(customer):
    to_encode = {
        'sub': customer.email
    }
    return create_token(to_encode)

@pytest.fixture
def test_db_session():
    connection_url = os.getenv("DB_TESTS")
    engine = create_engine(connection_url, echo=True)
    return sessionmaker(bind=engine)


@pytest.fixture
def client(test_db_session):
    app.dependency_overrides[get_db] = overrides_db
    client = TestClient(app)


    yield client

    db = test_db_session()

    db.execute(text('TRUNCATE TABLE orders, order_items, products, customers RESTART IDENTITY'))
    db.commit()
    db.close()
    app.dependency_overrides.clear()

@pytest.fixture
def admin_record(test_db_session):
    db = test_db_session()

    customer = Customer(
        email='test_customer',
        hashed_password='123',
        role='ADMIN'
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    db.close()

    return customer


@pytest.fixture
def customer_record(test_db_session):
    db = test_db_session()

    customer = Customer(
        email='test_customer',
        hashed_password='hashed_pwd',
        role='CUSTOMER'
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)
    db.close()

    return customer

@pytest.fixture
def product_records(test_db_session):
    print('products_fixture')
    db = test_db_session()

    product = Product(name='tv', price=10, stock_quantity=5)
    product1 = Product(name='phone', price=10, stock_quantity=5)

    db.add(product)
    db.add(product1)
    db.commit()

    db.refresh(product)
    db.refresh(product1)

    db.close()


    return product, product1

@pytest.fixture
def payload_items():
    return [
        SimpleNamespace(product_id=1, qty=1),
        SimpleNamespace(product_id=2, qty=1)
    ]

