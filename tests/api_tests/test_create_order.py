from models import Product
from conftest import customer_auth_token

def test_create_order_happy_path(client, customer_record, product_records, test_db_session):
    product, product1 = product_records
    auth_token = customer_auth_token(customer_record)

    response = client.post(
        url='/orders',
        headers={'Authorization': f'Bearer {auth_token}'},
        json = {
            'items': [
                {
                    'product_id': product.id,
                    'qty': 1
                },
                {
                    'product_id': product1.id,
                    'qty': 2
                }
            ]
        }
    )


    assert response.status_code==201
    assert response.json()['customer_id'] == customer_record.id
    assert response.json()['status'] == 'pending'
    assert response.json()['total_amount'] == (1 * product.price) + (2 * product1.price)

    db = test_db_session()
    product = db.get(Product, product.id)
    product1 = db.get(Product, product1.id)
    assert product.stock_quantity == 4
    assert product1.stock_quantity == 3
    db.close()


def test_create_order_unauthorized_customer(client):
    response = client.post(
        url='/orders',
        #no authorization header
        json = {
            'items': [
                {
                    'product_id': 1,
                    'qty': 1
                },
                {
                    'product_id': 2,
                    'qty': 2
                }
            ]
        }
    )
    assert response.status_code==401



def test_create_order_invalid_product(client, customer_record):
    auth_token = customer_auth_token(customer_record)

    response = client.post(
        url='/orders',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'items': [
                {
                    'product_id': 999999,
                    'qty': 1
                }
            ]
        }
    )

    assert response.status_code==404
    assert response.json()['detail'] == 'one or more product not found'

def test_create_order_invalid_product_stock(customer_record, product_records, client, test_db_session):
    product, product1 = product_records
    auth_token = customer_auth_token(customer_record)

    response = client.post(
        url='/orders',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'items': [
                {
                    'product_id': product.id,
                    'qty': 2
                },
                {
                    'product_id': product1.id,
                    'qty': 10
                }
            ]
        }
    )
    assert response.status_code==409
    assert response.json()['detail'] == 'not available stock for one or more products'

    db = test_db_session()
    product = db.get(Product, product.id)
    product1 = db.get(Product, product1.id)

    assert product.stock_quantity == 5
    assert product1.stock_quantity == 5
    db.close()



def test_create_order_invalid_request_item_qty(customer_record, client):
    auth_token = customer_auth_token(customer_record)

    response = client.post(
        '/orders',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'items': [
                {
                    'product_id': 1,
                    'qty': 0
                }
            ]
        }
    )

    assert response.status_code == 422

def test_create_order_total_amount_validation_for_same_id(customer_record, product_records, client, test_db_session):
    auth_token = customer_auth_token(customer_record)

    product, product1 = product_records

    response = client.post(
        '/orders',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'items': [
                {
                    'product_id': product.id,
                    'qty': 1
                },
                {
                    'product_id': product.id,
                    'qty': 3
                }
            ]
        }
    )
    assert response.status_code == 201
    assert response.json()['total_amount'] == 40

    db = test_db_session()
    product = db.get(Product, product.id)
    assert product.stock_quantity == 1
    db.close()









