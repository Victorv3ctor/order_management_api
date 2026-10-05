from security import verify_password, create_token, decode_token, DUMMY_HASH
from repositories.customer import get_customer_by_email
from exceptions import InvalidCredentialsError, NoPermissionError, InvalidSubCredentials, CustomerNotFound
from datetime import datetime, timezone, timedelta

def authenticate_customer(db, email, password):
    customer = get_customer_by_email(db, email)

    if not customer:
        verify_password(password, DUMMY_HASH)
        raise InvalidCredentialsError()

    if not verify_password(password, customer.hashed_password):
        raise InvalidCredentialsError()

    return customer

def create_access_token(customer):
    payload = {
        "sub": customer.email,
        "role": customer.role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
    }

    encoded_jwt = create_token(to_encode=payload.copy())
    return encoded_jwt

def validate_current_customer_from_token(token, db):
    payload = decode_token(token)
    customer_email = payload.get("sub")

    if not customer_email:
        raise InvalidSubCredentials()

    customer = get_customer_by_email(db, customer_email)
    if not customer:
        raise CustomerNotFound()

    return customer

def validate_require_admin(customer):
    if customer.role != "ADMIN":
        raise NoPermissionError()

def validate_filter_access(customer):
    if customer.role != "ADMIN":
        return customer.id
    return None