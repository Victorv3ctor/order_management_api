from repositories.order import get_paginated_orders_data, add_new_order, get_order_by_id, get_customer_order
from repositories.product import get_products_by_id, reduce_stock
from models import Order, OrderItem
from exceptions import ProductsValidationError, StockValidationError, OrderNotFoundError, StatusTransitionError
from schemas.order import OrderResponse
import json

def valid_order_status_transition(order_status, new_status):
    order_status_mapper = {
        'pending': ['paid', 'cancelled'],
        'paid': ['processing', 'cancelled'],
        'processing': ['shipped'],
        'shipped': ['completed']
    }

    allowed_statuses = order_status_mapper.get(order_status, None)

    if allowed_statuses is None or new_status not in allowed_statuses:
        raise StatusTransitionError()

    return new_status

def order_total_price_calculation(products_by_id, items):
    return sum(
        [
            products_by_id[item.product_id].price * item.qty for item in items
         ]
    )

def get_paginated_orders(
        db,
        page: int,
        page_size: int,
        status: str | None = None,
        sort: str | None = None,
        customer_id: int |None = None,
):
    offset = (page - 1) * page_size
    conditions = []
    sort_filter = None

    if status:
        conditions.append(Order.status == status)

    if customer_id:
        conditions.append(Order.customer_id == customer_id)

    if sort:
        sort_filters = {
            'total_amount': Order.total_amount,
            'created_at': Order.created_at,
            'order_id': Order.id
        }
        sort_filter = sort_filters.get(sort)

    orders, total = get_paginated_orders_data(
        db=db,
        offset=offset,
        limit=page_size,
        conditions=conditions,
        sort_filter=sort_filter
    )

    return {
        "items": orders,
        "page": page,
        "page_size": page_size,
        "total_count": total,
        "has_next_page": (page*page_size) < total,
        "has_previous_page": page > 1
    }

def create_new_order(db, items, customer):
    products_id = [order_item.product_id for order_item in items]
    products = get_products_by_id(db, products_id=products_id)

    if len(products) != len(set(products_id)):
        raise ProductsValidationError()

    order = Order(customer_id=customer.id, status="pending")

    for order_item in items:
        order.order_items.append(
            OrderItem(
                product_id=order_item.product_id,
                qty=order_item.qty
            )
        )
        result = reduce_stock(
            db=db,
            product_id=order_item.product_id,
            qty=order_item.qty
        )
        if result == 0:
            raise StockValidationError()

    products_by_id = {product.id: product for product in products}

    order.total_amount = order_total_price_calculation(
        products_by_id=products_by_id,
        items=items
    )
    add_new_order(db, order)
    return order

def order_status_transition(db, order_id, new_status):
    order = get_order_by_id(db, order_id)
    if not order:
        raise OrderNotFoundError()

    new_status = valid_order_status_transition(
        order_status=order.status,
        new_status=new_status
    )

    order.status = new_status
    db.commit()

    return order

def process_order_payment(db, cache, order_id, customer_id, idempotency_key):
    order = get_customer_order(
        db,
        order_id=order_id,
        customer_id=customer_id
    )

    if not order:
        raise OrderNotFoundError()

    key = f'{order.id}{customer_id}{idempotency_key}'

    cached_response = cache.get(key)
    if cached_response:
        return OrderResponse.model_validate(json.loads(cached_response))

    if order.status != 'pending':
        raise StatusTransitionError()

    order.status = 'paid'
    db.commit()

    response = OrderResponse.model_validate(order)
    json_response = OrderResponse.model_dump_json(response)

    cache.set(key, json_response, nx=True, ex=86400)

    return response