

def test_create_customer_happy_path(client):
    response = client.post(url='/customers', json={'name': 'test_wiktor', 'email': 'test@example.com'})
    assert response.status_code==201
    assert response.json()['name'] == 'test_wiktor'

def test_create_customer_fail_path(client):
    response1= client.post(url='/customers', json={'name': 'damian', 'email': 'damian@example.com'})
    assert response1.status_code==201
    assert response1.json()['email'] == 'damian@example.com'

    response1 = client.post(url='/customers', json={'name': 'dominik', 'email': 'damian@example.com'})
    assert response1.status_code == 409
    assert response1.json()['detail'] == 'email already exists'













