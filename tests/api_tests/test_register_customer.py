def test_register_customer_happy_path(client):
    response = client.post('/sign_in', json={'email': 'test_customer', 'password': 'hashed_pwd', 'role': 'CUSTOMER'})
    assert response.status_code==201
    assert response.json()['email'] == 'test_customer'

def test_register_customer_email_exists(client, customer_records):
    customer, customer1 = customer_records
    response = client.post('/sign_in', json={'email': customer.email, 'password': 'hashed_pwd'})
    assert response.status_code == 409
    assert response.json()['detail'] == 'user with this email exists'

def test_register_customer_wrong_credentials_type(client):
    #CustomerCreate => email: str, password: str
    response = client.post('/sign_in', json={'email': 123, 'password': 'password'})
    assert response.status_code==422














