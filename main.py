from database import get_db
from models import Customer, Product, Order, OrderItem
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import FastAPI, Depends, HTTPException

from schemas import (
    CustomerResponse, CustomerCreate, ProductCreate, ProductResponse,
    OrderResponse, OrderCreate, OrderStatusUpdate
)

from service import valid_status_transition, total_price_calculation
from repository import reduce_stock


app = FastAPI()

@app.post('/customers', response_model=CustomerResponse, status_code=201)
def add_new_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    customer = Customer(name=payload.name, email=payload.email)
    db.add(customer)
    try:
        db.commit()
    except IntegrityError:
        raise HTTPException(status_code=409, detail='email already exists')
    db.refresh(customer)
    return customer

@app.get('/customers/{customer_id}', response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail='customer id not found')
    return customer

@app.post('/orders', response_model=OrderResponse, status_code=201)
def create_order(payload: OrderCreate, db:Session=Depends(get_db)):
    customer = db.get(Customer, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail='customer id not found')

    products_id = [item.product_id for item in payload.items]

    stmt = select(Product).where(Product.id.in_(products_id))
    products = db.execute(stmt).scalars().all()


    if len(products) != len(set(products_id)):
        raise HTTPException(status_code=404, detail='one or more product not found')


    order = Order(customer_id=payload.customer_id, status="pending")

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

@app.patch('/orders/{order_id}', response_model = OrderResponse)
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

@app.get('/orders/{order_id}', response_model=OrderResponse)
def get_order(order_id:int, db:Session=Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail='order id not found')
    return order

@app.post('/products', response_model=ProductResponse, status_code=201)
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

@app.get('/products/{product_id}', response_model=ProductResponse)
def get_product(product_id:int, db:Session=Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail='product id not found')
    return product










