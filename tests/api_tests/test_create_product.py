
def test_create_product_happy_path(client):
    response = client.post(
        url='/products',
        json={'name': 'tv', 'price': 50, 'stock_quantity': 10}
    )
    assert response.status_code == 201
    assert response.json()['name'] == 'tv'

def test_create_product_fail_path(client):
    client.post(
        url='/products',
        json={'name': 'tv', 'price': 50, 'stock_quantity': 10}
    )
    response = client.post(
        url='/products',
        json={'name': 'tv', 'price': 50, 'stock_quantity': 10}
    )

    assert response.status_code==409
    assert response.json()['detail'] == 'product with this name exists'


