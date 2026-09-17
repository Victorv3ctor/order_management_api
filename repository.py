from sqlalchemy import update, and_, select, func
from sqlalchemy.orm import Session
from models import Product, Order, Customer

def reduce_stock(db: Session, product_id: int, qty: int):
    stmt = (
        update(Product)
        .where(
            and_(
                Product.id == product_id,
                Product.stock_quantity >= qty
            )
        )
        .values(
            stock_quantity=Product.stock_quantity - qty
        )
    )
    result = db.execute(stmt)
    return result.rowcount

def get_paginated_orders(
        db: Session,
        page: int,
        page_size: int,
        status: str | None = None,
        sort: str | None = None,
        customer_id: int |None = None,
):
    offset = (page - 1) * page_size
    conditions = []

    sort_filters = {
        'total_amount': Order.total_amount,
        'created_at': Order.created_at,
        'order_id': Order.id
    }

    if status:
        conditions.append(Order.status == status)

    if customer_id: #+++ if users asks for customer that doesnt exist, raise
        conditions.append(Order.customer_id == customer_id)

    stmt = (
        select(Order)
        .offset(offset)
        .limit(page_size)
        .where(*conditions)
    )

    if sort:
        stmt=stmt.order_by(sort_filters.get(sort).desc()) #hard coded desc

    orders = db.execute(stmt).scalars().all()


    stmt1 = select(func.count(Order.id)).where(*conditions)
    total_records = db.execute(stmt1).scalar()

    return {
        "items": orders,
        "page": page,
        "page_size": page_size,
        "total_count": total_records,
        "has_next_page": (page*page_size) < total_records,
        "has_previous_page": page > 1
    }

def get_customers_data(db: Session):
    stmt = select(Customer)
    customers = db.execute(stmt).scalars().all()

    return {
        "customers" : customers
    }

def get_paginated_products(
        db: Session,
        page: int,
        page_size : int,
        name: str | None = None,
        sort: str | None = None, #stock, #qty
        product_id: int | None = None,
):

    conditions = []

    sort_filters = {
        'price': Product.price,
        'stock': Product.stock_quantity
    }

    offset = (page - 1) * page_size

    stmt = (
        select(Product)
        .offset(offset)
        .limit(page_size)
        .where()
    )

    if product_id:
        conditions.append(Product.id==product_id)

    if name:
        conditions.append(Product.name.contains(name))

    if sort:
        stmt = stmt.order_by(sort_filters.get(sort).desc())

    products = db.execute(stmt).scalars().all()

    stmt1 = select(func.count(Product.id)).where(*conditions)
    total_count = db.execute(stmt1).scalar()



    return {
        'items': products,
        'page': page,
        'page_size': page_size,
        'total_count': total_count,
        'has_next_page': (page*page_size) < total_count,
        'has_previous_page': page > 1
    }






