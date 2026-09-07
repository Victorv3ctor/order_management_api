from models import Customer
from models import Product
import pytest

@pytest.fixture
def customer_and_product(test_db_session):
    db = test_db_session()
    customer = Customer(id=1, name='order_test', email='order_test@example.com')
    product = Product(id=1, name = 'tv', price=10, stock_quantity=5)
    product1 = Product(id=2, name = 'phone', price=10, stock_quantity=5)
    db.add(customer)
    db.add(product)
    db.add(product1)
    db.commit()
    db.close()
    #Przy wywolaniu tego fixture
    #na starcie funkcji testowej, wlatuje nam do bazy testowej
    #customer o id 1 do tabeli Customers
    # i product o id1 do tabeli Products i zamykamy polaczenie


#test zaczynamy z customer id1 i productid1 w bazie
def test_create_order_happy_path(customer_and_product, client):
    response = client.post(
        url='/orders',
        json = {
            'customer_id': 1,
            'items': [
                {
                    'product_id': 1,
                    'qty': 1
                },
                {
                    'product_id': 2,
                    'qty': 1
                }
            ]
        }
    )
    order_items = response.json()['order_items']

    assert response.status_code==201
    assert response.json()['customer_id'] == 1
    assert response.json()['status'] == 'pending'
    assert response.json()['total_amount'] == 20
    assert len(order_items) == 2


def test_create_order_invalid_customer(customer_and_product, client):
    response = client.post(
        url='/orders',
        json={
            'customer_id': 99,
            'items': [
                {
                    'product_id': 1,
                    'qty': 1
                }
            ]
        }
    )
    assert response.status_code==404
    assert response.json()['detail'] == 'customer id not found'



def test_create_order_invalid_product(customer_and_product, client):
    response = client.post(
        url='/orders',
        json={
            'customer_id': 1,
            'items': [
                {
                    'product_id': 3,
                    'qty': 1
                }
            ]
        }
    )

    assert response.status_code==404
    assert response.json()['detail'] == 'one or more product not found'

def test_create_order_invalid_product_stock(customer_and_product, client):
    response = client.post(
        url='/orders',
        json={
            'customer_id': 1,
            'items': [
                {
                    'product_id': 2,
                    'qty': 2
                },
                {
                    'product_id': 1,
                    'qty': 10
                }
            ]
        }
    )
    assert response.status_code==409
    assert response.json()['detail'] == 'not enough stock for one product or more'












