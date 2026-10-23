from database import get_db
from cache import get_cache
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException, Query, Header, Path, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.dependencies import get_current_customer, require_admin, filter_access
from typing import Annotated, Literal
from models import Customer
import logging
from fastapi import Response
from schemas.customer import CustomerCreate, CustomerResponse, CustomersInfoResponse
from schemas.order import OrderCreate, OrderResponse, PaginatedOrderResponse, OrderStatusUpdate
from schemas.product import ProductCreate, ProductResponse, PaginatedProductsResponse
from schemas.auth import TokenResponse
from schemas.health import HealthResponse
from services.customer import create_new_customer, get_all_customers
from services.auth import authenticate_customer, create_access_token
from services.order import get_paginated_orders, create_new_order, order_status_transition, process_order_payment
from services.product import get_paginated_products, create_new_product
from services.health import get_health_check
from exceptions import (
    EmailExistsError, InvalidCredentialsError, ProductNameExistsError, ProductsValidationError,
    OrderNotFoundError, StockValidationError, StatusTransitionError
)

logging.basicConfig(
    level=logging.INFO,
    format=" %(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

app = FastAPI(title='Order Management App')

@app.exception_handler(Exception)
def unexpected_exception_handler(request: Request, exc: Exception):
    logger.error(
        'request %s %s unexpected error',
        request.method, request.url.path,
        exc_info=exc
    )

    return JSONResponse(
        status_code=500,
        content={'detail':'unexpected app error'}
    )


@app.get('/health', status_code=200, response_model=HealthResponse, responses = {503: {"model": HealthResponse}})
def health_check(response: Response, db: Annotated[Session, Depends(get_db)], cache = Depends(get_cache)):
    health_response = get_health_check(db, cache)
    if health_response.status != 'health':
        response.status_code=503
    return health_response


@app.post('/sign_in', response_model=CustomerResponse, status_code=201)
def register(payload: CustomerCreate, db: Annotated[Session, Depends(get_db)]):
    try:
        customer = create_new_customer(
            payload_email=payload.email,
            payload_password=payload.password,
            db=db
        )
    except EmailExistsError as error:
        logger.warning('rejected attempt to add customer_email: %s  to db', payload.email)
        raise HTTPException(status_code=409, detail=error.detail)

    return customer


@app.post('/auth/login', response_model=TokenResponse)
def login_in(form_data=Depends(OAuth2PasswordRequestForm), db: Session = Depends(get_db)):
    try:
        customer = authenticate_customer(
            db=db,
            email=form_data.username,
            password=form_data.password
        )
    except InvalidCredentialsError as error:
        logger.warning('invalid login credentials for customer_email')
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
        logger.warning('rejected to add new product to database, product_name: %s ', payload.name)
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
    except ProductsValidationError as error:
        logger.warning('products validation error for products %s for customer_id: %s ', payload.items, current_customer.id)
        raise HTTPException(status_code=404, detail=error.detail)
    except StockValidationError as error:
        logger.warning('stock validation error for products %s  for customer_id: %s', payload.items, current_customer.id)
        raise HTTPException(status_code=409, detail=error.detail)


@app.patch('/orders/{order_id}', response_model = OrderResponse, dependencies=[Depends(require_admin)])
def change_order_status(payload: OrderStatusUpdate, order_id: Annotated[int, Path(ge=1)], db: Annotated[Session, Depends(get_db)]):
    try:
        return order_status_transition(
            db=db,
            order_id=order_id,
            new_status=payload.status
        )
    except OrderNotFoundError as error:
        logger.warning('order_id %s not found', order_id)
        raise HTTPException(status_code=404, detail=error.detail)
    except StatusTransitionError as error:
        logger.warning('status transition to %s rejected for order_id %s', payload.status, order_id)
        raise HTTPException(status_code=409, detail=error.detail)


@app.post('/orders/{order_id}/payment')
def order_payment(
        current_customer: Annotated[Customer, Depends(get_current_customer)],
        db: Annotated[Session, Depends(get_db)],
        idempotency_key: Annotated[str, Header()],
        order_id: Annotated[int, Path(ge=1)],
        cache=Depends(get_cache)
):
    try:
        return process_order_payment(
            db=db,
            cache=cache,
            order_id=order_id,
            customer_id=current_customer.id,
            idempotency_key=idempotency_key
        )

    except OrderNotFoundError as error:
        logger.warning('customer_id %s order_id %s not found', current_customer.id, order_id)
        raise HTTPException(status_code=404, detail=error.detail)
    except StatusTransitionError as error:
        logger.warning('customer_id %s status transition to paid rejected for order_id %s', current_customer.id, order_id)
        raise HTTPException(status_code=409, detail=error.detail)



