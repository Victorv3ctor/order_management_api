import pytest
from sqlalchemy import create_engine, update, and_
from sqlalchemy.orm import sessionmaker
from models import Product
from types import SimpleNamespace
from repository import reduce_stock


@pytest.fixture
def db_connection():
    connection_url  = "postgresql://postgres:postgres@localhost:5433/my_postgres_tests"
    engine = create_engine(connection_url)
    #engine - centralny element odpowiedzialny za zarzadzanie polaczeniami z baza

    SessionLocal = sessionmaker(bind=engine)
    #sessionmaker - fabryka generujaca sesje, SessioNlocal(to jej wynik)
    #bind=engine mowi z jakim enginem ma pracowac sesja

    db = SessionLocal() #pobranie sesji do zmiennej db

    product = Product(
        id=1,
        name='test_product',
        price=10,
        stock_quantity=10
    )

    product1= Product(
        id=2,
        name='test_product1',
        price=10,
        stock_quantity=10
    )

    db.add(product)
    db.add(product1)
    db.commit()
    #Wrzucenie dwoch produktow do tabeli Products my_postgres_tests database


    yield db

    #udostepnienie db do sesji

    #gdy test sie wykona, db wraca i od tego momentu usuwa wszystkie
    #wpisy do tabeli, na ktorych pracowala i zamyka polaczenie
    db.query(Product).delete()
    db.commit()
    db.close()




def test_stock_validation_stock_available(db_connection, payload_items):
    for order_item in payload_items:
        result = reduce_stock(db=db_connection, product_id=order_item.product_id, qty=order_item.qty)

        product = db_connection.get(Product, order_item.qty)

        assert result == 1
        assert product.stock_quantity == 9


def test_stock_validation_request_bigger_then_stock(db_connection):
    payload_items = [
        SimpleNamespace(product_id=1, qty=9999)
    ]

    for order_item in payload_items:
        result = reduce_stock(db=db_connection, product_id=order_item.product_id, qty=order_item.qty)
        assert result == 0






