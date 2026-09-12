import pytest
from models import Order
from models import Customer
import datetime

@pytest.fixture
def orders(test_db_session):
    customer = Customer(id=1, name='test', email='test@')
    customer1 = Customer(id=2, name='test1', email='test1@')

    order = Order(
        id=1,
        customer_id=1,
        total_amount=20,
        status='pending',
        created_at=datetime.datetime(2020,1,1)
    )
    order1 = Order(
        id=2,
        customer_id=2,
        total_amount=300,
        status='paid',
        created_at=datetime.datetime(2020,1,2)
    )

    db = test_db_session()

    db.add(customer)
    db.add(customer1)
    db.add(order)
    db.add(order1)
    db.commit()

    db.close()

def test_get_order_happy_path_pagination(orders, client):
    response = client.get(url='/orders?page=1&page_size=3')

    response_items = response.json()["items"]

    assert len(response_items) == 2
    assert response.status_code==200
    assert response.json()["page"] == 1
    assert response.json()["page_size"] == 3
    assert response.json()["total_count"] == 2
    assert response.json()["has_previous_page"] is False

def test_get_order_fail_page(orders, client):
    response = client.get(url='/orders?page=-1&page_size=3')
    assert response.status_code == 422

def test_get_order_fail_page_size(orders, client):
    response = client.get(url='/orders?page=1&page_size=0')
    assert response.status_code == 422

def test_get_order_happy_path_with_status(orders, client):
    response = client.get(url='/orders?page=1&page_size=3&status=paid')

    response_items = response.json()["items"]

    assert len(response_items) == 1
    assert all([item["status"]=='paid' for item in response_items])
    assert not any([item["status"]!='paid' for item in response_items])
    assert response.json()["total_count"] == 1

def test_get_order_failed_status(orders, client):
    response = client.get(url='/orders?page=1&page_size=3&status=non_literal_status')

    assert response.status_code == 422

def test_get_order_with_existing_customer_id(orders, client):
    response = client.get(url='/orders?page=1&page_size=3&customer_id=2')

    response_items = response.json()["items"]
    assert len(response_items) == 1
    assert all([item["customer_id"] == 2 for item in response_items])
    assert not any(item["customer_id"] != 2 for item in response_items)

#Not raised yet
def test_get_order_with_non_existing_customer_id(orders, client):
    response = client.get(url='/orders?page=1&page_size=3&customer_id=5')

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total_count"] == 0


#sort works with desc
def test_get_order_with_sort_total_amount_arg(orders, client):
    response = client.get(url='/orders?page=1&page_size=3&sort=total_amount')

    response_items = response.json()["items"]
    first_item = response_items[0]
    second_item = response_items[1]

    assert first_item["total_amount"] > second_item["total_amount"]
    assert first_item["customer_id"] == 2


def test_get_order_with_sort_created_at_arg(orders, client):
    response = client.get(url='/orders?page=1&page_size=3&sort=created_at')

    response_items = response.json()["items"]
    first_item = response_items[0]
    second_item = response_items[1]

    assert first_item["created_at"] > second_item["created_at"]
    assert first_item["customer_id"] == 2


def test_get_order_with_sort_order_id_arg(orders, client):
    response = client.get(url='/orders?page=1&page_size=3&sort=order_id')

    response_items = response.json()["items"]
    first_item = response_items[0]
    second_item = response_items[1]

    assert first_item["id"] > second_item["id"]
    assert first_item["customer_id"] == 2












