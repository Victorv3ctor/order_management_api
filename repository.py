from sqlalchemy import update, and_
from sqlalchemy.orm import Session
from models import Product

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

