from database import get_db
from models import Customer, Product, Order, OrderItem
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import FastAPI, Depends, HTTPException, Query

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated, Literal
from pwdlib import PasswordHash
import jwt
from jwt.exceptions import  InvalidSignatureError, ExpiredSignatureError
from datetime import timedelta, datetime, timezone

from schemas import (
    CustomerResponse, CustomerCreate, ProductCreate, ProductResponse,
    OrderResponse, OrderCreate, OrderStatusUpdate, PaginatedOrderResponse,
    TokenResponse, CustomersResponse, PaginatedProductsResponse
)
import os
from dotenv import load_dotenv
from service import valid_status_transition, total_price_calculation
from repository import reduce_stock, get_paginated_orders, get_customers_data, get_paginated_products

load_dotenv() #explicit better than implicit

app = FastAPI()

"""SECURITY"""
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash(os.getenv('DUMMY_PASSWORD'))

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRES_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRES_MINUTES'))


def get_hashed_password(plain_password: str):
    return password_hash.hash(plain_password)

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def authenticate_customer(db, username: str, password: str):
    stmt = select(Customer).where(Customer.email==username)
    customer = db.execute(stmt).scalar()

    if not customer:
        password_hash.verify(password, DUMMY_HASH)
        return False

    if not password_hash.verify(password, customer.hashed_password):
        return False

    return customer


def create_access_token(data: dict, expires_delta: int | None = None):
    to_encode = data.copy()
    if expires_delta:
        expires = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    else:
        expires = datetime.now(timezone.utc) + timedelta(minutes=30)

    to_encode.update({"exp": expires})

    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

    return encoded_jwt

def get_current_customer(
        db: Annotated[Session, Depends(get_db)],
        token: Annotated[str, Depends(oauth2_scheme)]
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid SignatureError")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token Expired")

    customer_email = payload.get("sub")
    if not customer_email:
        raise HTTPException(status_code=401, detail="Could not validate Credentials")

    stmt = select(Customer).where(Customer.email==customer_email)
    customer = db.execute(stmt).scalar()

    if not customer:
        raise HTTPException(status_code=401, detail="Could not validate Credentials, No result for Credentials")

    return customer


def require_admin(customer: Customer=Depends(get_current_customer)):
    if customer.role != "ADMIN":
        raise HTTPException(status_code=403, detail="No Permission")

def filter_access(customer: Customer=Depends(get_current_customer)):
    if customer.role != "ADMIN":
        return customer.id
    return None





"""ENDPOINTS"""

@app.post('/sign_in', response_model=CustomerResponse, status_code=201)
def sing_in(payload: CustomerCreate, db: Session = Depends(get_db)):
    hashed_password = get_hashed_password(payload.password)

    customer = Customer(
        email=payload.email, hashed_password=hashed_password, role="CUSTOMER"
    )

    db.add(customer)
    try:
        db.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail='email already exists')
    db.refresh(customer)
    return customer

@app.post('/auth/login')
def login_in(form_data=Depends(OAuth2PasswordRequestForm), db: Session = Depends(get_db)):
    customer = authenticate_customer(
        db=db,
        username=form_data.username,
        password=form_data.password
    )
    if not customer:
        raise HTTPException(status_code=401, detail="INCORRECT USERNAME OR PASSWORD")

    access_token = create_access_token(
        data={"sub": customer.email, "role": customer.role}, expires_delta=ACCESS_TOKEN_EXPIRES_MINUTES
    )

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
        customer_id=customer_id,
        sort=sort
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
def add_product(payload: ProductCreate, db:Session=Depends(get_db)):
    product = Product(
        name=payload.name, price=payload.price, stock_quantity=payload.stock_quantity
                      )

    db.add(product)
    try:
        db.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail='product with this name exists')

    db.refresh(product)
    return product

@app.get('/customers/me', response_model=CustomerResponse)
def get_customers_me(current_customer: Annotated[Customer, Depends(get_current_customer)], db: Session = Depends(get_db)) :
    customer = db.get(Customer, current_customer.id)
    if not customer:
        raise HTTPException(status_code=404, detail='customer id not found')
    return customer

@app.get('/customers', dependencies=[Depends(require_admin)], response_model=CustomersResponse)
def get_all_customers_data(db: Session = Depends(get_db)):
    return get_customers_data(db)

@app.post('/orders', response_model=OrderResponse, status_code=201)
def create_order(payload: OrderCreate, current_customer=Depends(get_current_customer), db:Session=Depends(get_db)):
    products_id = [order_item.product_id for order_item in payload.items]

    stmt = select(Product).where(Product.id.in_(products_id))
    products = db.execute(stmt).scalars().all()

    if len(products) != len(set(products_id)):
        raise HTTPException(status_code=404, detail='one or more product not found')

    order = Order(customer_id=current_customer.id, status="pending")

    for order_item in payload.items:
        order.order_items.append(
            OrderItem(product_id=order_item.product_id, qty=order_item.qty)
        )

        result = reduce_stock(db=db, product_id=order_item.product_id, qty=order_item.qty)
        if result == 0:
            raise HTTPException(status_code=409, detail='not enough stock for one product or more')


    products_by_id = {product.id: product for product in products}

    order.total_amount = total_price_calculation(
        products_by_id=products_by_id,
        payload_items=payload.items
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order

@app.patch('/orders/{order_id}', response_model = OrderResponse, dependencies=[Depends(require_admin)])
def change_order_status(order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail='order id not found')

    new_status = valid_status_transition(
        order_status=order.status,
        payload_status=payload.status
    )

    if new_status is None:
        raise HTTPException(status_code=409, detail='transition not allowed')

    order.status = payload.status
    db.commit()
    db.refresh(order)

    return order











