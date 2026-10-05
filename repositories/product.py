from sqlalchemy import update, and_, select, func
from sqlalchemy.exc import IntegrityError
from exceptions import ProductNameExistsError
from models import Product

def reduce_stock(db, product_id: int, qty: int):
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

def get_paginated_products_data(
        db,
        offset: int,
        limit : int,
        conditions: list,
        sort_filter = None
):

    stmt = (
        select(Product)
        .offset(offset)
        .limit(limit)
        .where(*conditions)
    )

    if sort_filter:
        stmt = stmt.order_by(sort_filter.desc())

    products = db.execute(stmt).scalars().all()

    stmt1 = select(func.count(Product.id)).where(*conditions)
    total = db.execute(stmt1).scalar()

    return products, total

def add_new_product(db, product):
    db.add(product)
    try:
        db.commit()
    except IntegrityError as error:
        if 'products_name_key' in str(error):
            raise ProductNameExistsError()

def get_products_by_id(db, products_id: list):
    stmt = select(Product).where(Product.id.in_(products_id))
    products = db.execute(stmt).scalars().all()
    return products