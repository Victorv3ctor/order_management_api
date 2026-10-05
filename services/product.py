from models import Product
from repositories.product import get_paginated_products_data, add_new_product

def get_paginated_products(
        db,
        page,
        page_size,
        name,
        product_id,
        sort
):
    offset = (page-1) * page_size
    conditions = []
    sort_filter = None

    if name:
        conditions.append(Product.name.contains(name))

    if product_id:
        conditions.append(Product.id==product_id)

    if sort:
        sort_filters = {
            'price': Product.price,
            'stock': Product.stock_quantity
        }
        sort_filter = sort_filters.get(sort)

    products, total = get_paginated_products_data(
        db=db,
        offset=offset,
        limit=page_size,
        conditions=conditions,
        sort_filter=sort_filter
    )

    return {
        'items': products,
        'page': page,
        'page_size': page_size,
        'total_count': total,
        'has_next_page': (page*page_size) < total,
        'has_previous_page': page > 1
    }

def create_new_product(
        db,
        name,
        price,
        stock_qty
    ):
    product = Product(
        name=name,
        price=price,
        stock_quantity=stock_qty
    )

    add_new_product(db, product)
    return product
