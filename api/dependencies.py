from fastapi import Depends, HTTPException
from database import get_db
from security import oauth2_scheme
from services.auth import validate_current_customer_from_token, validate_require_admin, validate_filter_access
from exceptions import SignatureError, ExpiredTokenError, InvalidSubCredentials, CustomerNotFound, NoPermissionError
from models import Customer

def get_current_customer(
        db = Depends(get_db),
        token = Depends(oauth2_scheme)
):
    try:
        customer = validate_current_customer_from_token(token, db)
    except SignatureError as error:
        raise HTTPException(status_code=401, detail=error.detail)
    except ExpiredTokenError as error:
        raise HTTPException(status_code=401, detail=error.detail)

    except InvalidSubCredentials as error:
        raise HTTPException(status_code=401, detail=error.detail)
    except CustomerNotFound as error:
        raise HTTPException(status_code=401, detail=error.detail)

    return customer

def require_admin(customer: Customer=Depends(get_current_customer)):
    try:
        validate_require_admin(customer)
    except NoPermissionError as error:
        raise HTTPException(status_code=401, detail=error.detail)

def filter_access(customer: Customer=Depends(get_current_customer)):
    return validate_filter_access(customer)
