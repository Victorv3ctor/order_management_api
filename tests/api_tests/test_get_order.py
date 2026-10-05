import pytest
from models import Order, Customer
import datetime
from conftest import customer_auth_token

@pytest.fixture
def customers_records(test_db_session): #add 2 record to customers table
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
def order_records(customers_records, test_db_session): #creates 2 order records in table orders
    customer, customer1 = customers_records

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

def test_get_order_happy_path_customer_role(client, order_records, customers_records):
    customer, customer1 = customers_records

    auth_token = customer_auth_token(customer)

    response = client.get(
        url='/orders?page=1&page_size=3',
        headers={'Authorization': f'Bearer {auth_token}'}
    )

    assert response.status_code==200
    assert response.json()['has_next_page'] == False
    assert response.json()['has_previous_page'] == False
    assert response.json()['total_count'] == 1

    items = response.json()['items']
    assert all(item['customer_id']==customer.id for item in items)
    assert len(items) == 1

def test_get_order_happy_path_admin_role(client, order_records, admin_record):
    admin_auth_token = customer_auth_token(admin_record)

    response = client.get(
        url='/orders?page=1&page_size=3',
        headers={'Authorization': f'Bearer {admin_auth_token}'}
    )

    assert response.status_code==200
    assert response.json()['total_count'] == 2

    items = response.json()['items']
    assert not all(item['customer_id'] == admin_record.id for item in items)


def test_get_order_fail_input_validation(client, customer_record):
    auth_token = customer_auth_token(customer_record)

    response = client.get(
        url='/orders?page=-1&page_size=3',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 422

def test_get_order_unauthorized_request(client):
    response = client.get(
        url='/orders?page=-1&page_size=3',

    )
    assert response.status_code == 401
    assert response.json()['detail'] == 'Not authenticated'


def test_get_order_with_not_found_status(client, customers_records, order_records):
    customer, customer1 = customers_records

    auth_token = customer_auth_token(customer)

    response = client.get(
        url='/orders?page=1&page_size=3&status=shipped',
        headers={'Authorization': f'Bearer {auth_token}'}
    )

    assert response.status_code==200
    assert response.json()['items'] == []


def test_get_order_with_status(client, customers_records, order_records):
    customer, customer1 = customers_records

    auth_token = customer_auth_token(customer1)

    response = client.get(
        url='/orders?page=1&page_size=3&status=paid',
        headers={'Authorization': f'Bearer {auth_token}'}
    )

    assert response.status_code==200
    assert len(response.json()['items']) == 1
    assert response.json()['total_count'] == 1













