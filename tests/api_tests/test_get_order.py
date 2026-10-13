from conftest import customer_auth_token


def test_get_order_happy_path_customer_role(client, order_records, customer_records):
    customer, customer1 = customer_records

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


def test_get_order_fail_input_validation(client, customer_records):
    customer, customer1 = customer_records
    auth_token = customer_auth_token(customer)

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


def test_get_order_with_not_found_status(client, customer_records, order_records):
    customer, customer1 = customer_records

    auth_token = customer_auth_token(customer)

    response = client.get(
        url='/orders?page=1&page_size=3&status=shipped',
        headers={'Authorization': f'Bearer {auth_token}'}
    )

    assert response.status_code==200
    assert response.json()['items'] == []


def test_get_order_with_status(client, customer_records, order_records):
    customer, customer1 = customer_records

    auth_token = customer_auth_token(customer1)

    response = client.get(
        url='/orders?page=1&page_size=3&status=paid',
        headers={'Authorization': f'Bearer {auth_token}'}
    )

    assert response.status_code==200
    assert len(response.json()['items']) == 1
    assert response.json()['total_count'] == 1













