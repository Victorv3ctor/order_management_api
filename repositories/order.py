from sqlalchemy import select, func
from models import Order

def get_paginated_orders_data(
        db,
        offset,
        limit,
        conditions,
        sort_filter = None
):
    stmt = (
        select(Order)
        .limit(limit)
        .offset(offset)
        .where(*conditions)
    )

    if sort_filter:
        stmt=stmt.order_by(sort_filter.desc())

    orders = db.execute(stmt).scalars().all()

    stmt1 = select(func.count(Order.id)).where(*conditions)
    total = db.execute(stmt1).scalar()

    return orders, total

def get_customer_order(db, order_id: int, customer_id: int):
    stmt = select(Order).where(Order.id==order_id, Order.customer_id==customer_id)
    order = db.execute(stmt).scalar()

    return order

def add_new_order(db, order):
    db.add(order)
    db.commit()

def get_order_by_id(db, order_id):
    order = db.get(Order, order_id)
    return order