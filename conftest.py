import pytest
from app.main import app
from types import SimpleNamespace
from fastapi.testclient import TestClient
from app.database import get_db
from app.cache import get_cache
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import Customer, Product, Order
from app.security import create_token
import os
from dotenv import load_dotenv
import datetime
import fakeredis
from app.models import Base
load_dotenv()


@pytest.fixture(scope="session", autouse=True)
def create_test_database_tables():
    if os.getenv("CI") == "true":
        yield
        return

    connection_url = os.getenv("DB_TESTS")
    engine = create_engine(connection_url, echo=True)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


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


"get_cache DUMMY"
@pytest.fixture
def cache_override():
    cache = fakeredis.FakeStrictRedis(decode_responses=True)
    return cache


def customer_auth_token(customer):
    to_encode = {
        'sub': customer.email
    }
    return create_token(to_encode)


@pytest.fixture
def order_records(customer_records, test_db_session): #creates 2 order records in table orders
    customer, customer1 = customer_records

    order = Order(
        customer_id=customer.id, #id 1
        total_amount=20,
        status='pending',
        created_at=datetime.datetime(2020,1,1)
    )

    order1 = Order(
        customer_id=customer1.id, #id 2
        total_amount=300,
        status='paid',
        created_at=datetime.datetime(2020,1,2)
    )

    db = test_db_session()

    db.add(order)
    db.add(order1)
    db.commit()
    db.refresh(order)
    db.refresh(order1)

    db.close()

    return order, order1

@pytest.fixture
def test_db_session():
    connection_url = os.getenv("DB_TESTS")
    engine = create_engine(connection_url, echo=True)
    return sessionmaker(bind=engine)


@pytest.fixture
def client(test_db_session, cache_override):
    app.dependency_overrides[get_db] = overrides_db
    app.dependency_overrides[get_cache] = lambda: cache_override
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
def customer_records(test_db_session):
    db = test_db_session()

    customer = Customer(
        email='test_customer0',
        hashed_password='hashed_pwd',
        role='CUSTOMER'
    )

    customer1 = Customer(
        email='test_customer1',
        hashed_password='hashed_pwd1',
        role='CUSTOMER'
    )

    db.add(customer)
    db.add(customer1)
    db.commit()
    db.refresh(customer)
    db.refresh(customer1)
    db.close()

    return customer, customer1

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

