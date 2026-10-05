from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from exceptions import EmailExistsError
from models import Customer

def get_customers(db):
    stmt = select(Customer)
    customers = db.execute(stmt).scalars().all()

    return customers

def add_new_customer(db, customer):
    db.add(customer)
    try:
        db.commit()
    except IntegrityError as error:
        if 'customers_email_key' in str(error):
            raise EmailExistsError() from error

def get_customer_by_email(db, email):
    stmt = select(Customer).where(Customer.email==email)
    customer = db.execute(stmt).scalar()
    return customer