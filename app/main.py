from database import get_db
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException, Query, Header, Path
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated, Literal
import redis
import os
from dotenv import load_dotenv

from models import Customer
from exceptions import (
    EmailExistsError, InvalidCredentialsError, ProductNameExistsError, ProductsValidationError,
    OrderNotFoundError, StockValidationError, StatusTransitionError
)
from dependencies import get_current_customer, require_admin, filter_access

from schemas.customer import CustomerCreate, CustomerResponse, CustomersInfoResponse
from schemas.order import OrderCreate, OrderResponse, PaginatedOrderResponse, OrderStatusUpdate
from schemas.product import ProductCreate, ProductResponse, PaginatedProductsResponse
from schemas.auth import TokenResponse

from services.customer import create_new_customer, get_all_customers
from services.auth import authenticate_customer, create_access_token
from services.order import get_paginated_orders, create_new_order, order_status_transition, process_order_payment
from services.product import get_paginated_products, create_new_product

load_dotenv()

app = FastAPI()
cache = redis.Redis(host=os.getenv('REDIS_HOST'), port=6379, decode_responses=True)


@app.post('/sign_in', response_model=CustomerResponse, status_code=201)
def register(payload: CustomerCreate, db: Annotated[Session, Depends(get_db)]):
    try:
        customer = create_new_customer(
            payload_email=payload.email,
            payload_password=payload.password,
            db=db
        )
    except EmailExistsError as error:
        raise HTTPException(status_code=409, detail=error.detail)

    return customer

@app.post('/auth/login')
def login_in(form_data=Depends(OAuth2PasswordRequestForm), db: Session = Depends(get_db)):
    try:
        customer = authenticate_customer(
            db=db,
            email=form_data.username,
            password=form_data.password
        )
    except InvalidCredentialsError as error:
        raise HTTPException(status_code=401, detail=error.detail)

    access_token = create_access_token(customer)

    return TokenResponse(access_token=access_token, token_type= "bearer")

@app.get('/orders', response_model=PaginatedOrderResponse)
def get_orders(
        page: Annotated[int, Query(ge=1)],
        page_size: Annotated[int, Query(ge=1, le=20)],
        status: Literal["paid", "cancelled", "processing", "shipped", "completed"] | None = None,
        sort: Literal["total_amount", "created_at", "order_id"] | None = None,
        customer_id: Annotated[int, Depends(filter_access)] = None,
        db:Session=Depends(get_db)
        ):

    return get_paginated_orders(
        db=db,
        page=page,
        page_size=page_size,
        status=status,
        sort=sort,
        customer_id=customer_id,
    )

@app.get('/products', response_model=PaginatedProductsResponse)
def get_products(
        page: Annotated[int, Query(ge=1)],
        page_size: Annotated[int, Query(ge=1, le=20)],
        sort: Literal["price", "stock"] | None = None,
        name: Annotated[str, Query()] = None,
        product_id: Annotated[int, Query(ge=1)] = None,
        db: Session = Depends(get_db)
        ):

    return get_paginated_products(
        db=db,
        page=page,
        page_size=page_size,
        sort=sort,
        name=name,
        product_id=product_id
    )

@app.post('/products', response_model=ProductResponse, status_code=201, dependencies=[Depends(require_admin)])
def add_product(payload: ProductCreate, db: Annotated[Session, Depends(get_db)]):
    try:
        return create_new_product(
            db=db,
            name=payload.name,
            price=payload.price,
            stock_qty=payload.stock_quantity
        )

    except ProductNameExistsError as error:
        raise HTTPException(status_code=409, detail=error.detail)

@app.get('/customers/me', response_model=CustomerResponse)
def get_customers_me(current_customer: Annotated[Customer, Depends(get_current_customer)]) :
    return current_customer

@app.get('/customers', response_model=CustomersInfoResponse, dependencies=[Depends(require_admin)])
def get_all_customers_data(db: Annotated[Session, Depends(get_db)]):
    return get_all_customers(db)



@app.post('/orders', response_model=OrderResponse, status_code=201)
def create_order(payload: OrderCreate, current_customer: Annotated[Customer, Depends(get_current_customer)], db: Annotated[Session, Depends(get_db)]):
    try:
        return create_new_order(
            db=db,
            items=payload.items,
            customer=current_customer
        )
    except ProductsValidationError as err:
        raise HTTPException(status_code=404, detail=err.detail)
    except StockValidationError as err:
        raise HTTPException(status_code=409, detail=err.detail)

@app.patch('/orders/{order_id}', response_model = OrderResponse, dependencies=[Depends(require_admin)])
def change_order_status(order_id: Annotated[int, Path(ge=1)], payload: OrderStatusUpdate, db: Annotated[Session, Depends(get_db)]):
    try:
        return order_status_transition(
            db=db,
            order_id=order_id,
            new_status=payload.status
        )
    except OrderNotFoundError as err:
        raise HTTPException(status_code=404, detail=err.detail)
    except StatusTransitionError as err:
        raise HTTPException(status_code=409, detail=err.detail)

@app.post('/orders/{order_id}/payment')
def order_payment(
        current_customer: Annotated[Customer, Depends(get_current_customer)],
        db: Annotated[Session, Depends(get_db)],
        idempotency_key: Annotated[str, Header()],
        order_id: Annotated[int, Path(ge=1)],
):
    try:
        return process_order_payment(
            db=db,
            cache=cache,
            order_id=order_id,
            customer_id=current_customer.id,
            idempotency_key=idempotency_key
        )
    except OrderNotFoundError as err:
        raise HTTPException(status_code=404, detail=err.detail)
    except StatusTransitionError as err:
        raise HTTPException(status_code=409, detail=err.detail)



