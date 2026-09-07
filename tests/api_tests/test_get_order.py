import pytest
from models import Order
from models import Customer

@pytest.fixture
def order(test_db_session):
    customer = Customer(id=1, name='test', email='test@')
    order = Order(id=1, customer_id=1, total_amount=20, status='pending')
    db = test_db_session()
    db.add(customer)
    db.add(order)
    db.commit()
    db.close()

def test_get_order_happy_path(order, client):
    response = client.get(url='/orders/1')
    assert response.status_code==200
    assert response.json()['customer_id'] == 1
    assert response.json()['total_amount'] == 20
    assert response.json()['status'] == 'pending'

def test_get_order_invalid_order_id(order, client):
    response = client.get(url='/orders/3')
    assert response.status_code == 404
    assert response.json()['detail'] == 'order id not found'







