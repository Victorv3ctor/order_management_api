from security import get_hashed_password
from models import Customer
from repositories.customer import add_new_customer, get_customers


def create_new_customer(db, payload_email, payload_password):
    hashed_password = get_hashed_password(payload_password)

    customer = Customer(
        email=payload_email, hashed_password=hashed_password, role='CUSTOMER'
    )

    add_new_customer(db, customer)

    return customer

def get_all_customers(db):
    customers = get_customers(db)

    return {
        'customers': customers
    }