from app.models import Order
from conftest import customer_auth_token

def test_order_payment_single_request(client, customer_records, order_records, cache_override, test_db_session):
    customer, customer1 = customer_records
    order, order1 = order_records
    auth_token = customer_auth_token(customer)

    assert order.status == 'pending'

    response = client.post(
        url=f'/orders/{order.id}/payment',
        headers={
            'Authorization': f'Bearer {auth_token}',
            'idempotency-key': '00'
        }
    )
    #key that is cashed is str created from order.id, customer_id, idempotency_key
    assert response.status_code==200

    db = test_db_session()
    order_after_payment = db.get(Order, order.id)
    db.close()

    assert order_after_payment.status=='paid'
    cached_key = f'{'1'}:{customer.id}:{'00'}'
    assert cached_key in cache_override.keys()

def test_order_payment_double_rq(client, customer_records, order_records, cache_override, test_db_session):
    customer, customer1 = customer_records
    order, order1 = order_records
    auth_token = customer_auth_token(customer)

    response = client.post(
        url=f'/orders/{order.id}/payment',
        headers={
            'Authorization': f'Bearer {auth_token}',
            'idempotency-key': '00'
        }
    )

    assert response.status_code==200
    key = f'{order.id}:{customer.id}:{'00'}'
    assert key in cache_override.keys()

    db = test_db_session()
    order_after_rq = db.get(Order, order.id)
    db.close()

    assert order_after_rq.status == 'paid'


    response1 = client.post(
        url=f'/orders/{order.id}/payment',
        headers={
            'Authorization': f'Bearer {auth_token}',
            'idempotency-key': '00'
        }
    )

    assert response1.status_code==200
    assert key in cache_override.keys()
    assert len(cache_override.keys()) == 1
    assert response.json() == response1.json()


def test_not_exist_order_payment(client, customer_records, order_records, cache_override):
    customer, customer1 = customer_records
    auth_token = customer_auth_token(customer)

    response = client.post(
        url=f'/orders/9999/payment',
        headers={
            'Authorization': f'Bearer {auth_token}',
            'idempotency-key': '00'
        }
    )

    #key that is cashed is str created from order.id, customer_id, idempotency_key
    key = f'{'9999'}{customer.id}{'00'}'
    assert key not in cache_override.keys()
    assert response.status_code==404
    assert response.json()['detail'] == 'order not found'

def test_wrong_customer_order(client, customer_records, order_records, cache_override, test_db_session):
    customer, customer1 = customer_records
    order, order1 = order_records
    #order1.customer_id ==  customer1.id


    auth_token = customer_auth_token(customer1) #jwt token for customer

    response = client.post(
        url=f'/orders/{order.id}/payment',
        headers={
            'Authorization': f'Bearer {auth_token}',
            'idempotency-key': '00'
        }
    )

    assert response.status_code==404
    assert response.json()['detail'] == 'order not found'

    db = test_db_session()
    order_after_rq = db.get(Order, order.id)
    db.close()
    assert order_after_rq.status == 'pending'


def test_unpayable_order_status(client, customer_records, order_records, cache_override):
    customer, customer1 = customer_records
    order, order1 = order_records #order1 status from conftest by default is paid
    auth_token = customer_auth_token(customer1)

    response = client.post(
        url=f'/orders/{order1.id}/payment',
        headers={
            'Authorization': f'Bearer {auth_token}',
            'idempotency-key': '00'
        }
    )

    assert response.status_code==409
    assert response.json()['detail'] == "transition not allowed for current order status"















