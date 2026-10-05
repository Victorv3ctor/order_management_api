from conftest import customer_auth_token

def test_add_product_happy_path(client, admin_record):
    auth_token = customer_auth_token(admin_record)

    response = client.post(
        url='/products',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'name': 'Phone',
            'price': 100,
            'stock_quantity': 10
        }
    )

    assert response.status_code==201
    assert response.json()['name'] == 'Phone'
    assert response.json()['price'] == 100
    assert response.json()['stock_quantity'] == 10


def test_add_product_unauthorized_role(client, customer_record):
    auth_token = customer_auth_token(customer_record)

    response = client.post(
        url='/products',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'name': 'TV',
            'price': 100,
            'stock_quantity': 10
        }
    )

    assert response.status_code==401
    assert response.json()['detail'] == 'no permission'

def test_add_product_name_duplicate(client, admin_record, product_records):
    auth_token = customer_auth_token(admin_record)

    product, product1 = product_records

    response = client.post(
        url='/products',
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'name': product.name,
            'price': 100,
            'stock_quantity': 10
        }
    )

    assert response.status_code==409
    assert response.json()['detail'] == 'product name exists'


def test_add_product_unauthorized(client):
    response = client.post(
        url='/products',
        #no authorization header
        json={
            'name': 'TV',
            'price': 100,
            'stock_quantity': 10
        }
    )

    assert response.status_code==401







