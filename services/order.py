from repositories.order import order_status_atomic_transition, order_payment_status_transition, get_paginated_orders_data, add_new_order, get_order_by_id, get_customer_order
from repositories.product import get_products_by_id, reduce_stock
from cache import get_from_cache, set_cache_response
from models import Order, OrderItem
from exceptions import CacheError, ProductsValidationError, StockValidationError, OrderNotFoundError, StatusTransitionError
from schemas.order import OrderResponse
import json
import logging


logger = logging.getLogger(__name__)


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
    payload_products_id = [order_item.product_id for order_item in items]
    products = get_products_by_id(db, products_id=payload_products_id)

    if len(products) != len(set(payload_products_id)):
        raise ProductsValidationError()

    order = Order(customer_id=customer.id, status="pending")

    for item in items:
        order.order_items.append(
            OrderItem(
                product_id=item.product_id,
                qty=item.qty
            )
        )
        result = reduce_stock(
            db=db,
            product_id=item.product_id,
            qty=item.qty
        )
        if result == 0:
            raise StockValidationError()


    products_by_id = {product.id: product for product in products}

    order.total_amount = order_total_price_calculation(
        products_by_id=products_by_id,
        items=items
    )

    add_new_order(db, order)
    db.commit()
    logger.info('customer_id %s order_id %s saved to database', order.customer_id, order.id)
    return order


def allowed_statuses_to_change_for_new_status(new_status):
    order_status_mapper = {
        'pending': ['paid', 'cancelled'],
        'paid': ['processing', 'cancelled'],
        'processing': ['shipped'],
        'shipped': ['completed']
    }


    return [
        status for status, allowed in order_status_mapper.items()
        if new_status in allowed
    ]


def order_status_transition(db, order_id, new_status):
    order = get_order_by_id(db, order_id)
    if not order:
        raise OrderNotFoundError()

    allowing_statuses = allowed_statuses_to_change_for_new_status(new_status)

    result = order_status_atomic_transition(
        db=db,
        order=order,
        allowing_statuses=allowing_statuses,
        new_status=new_status
    )

    if result == 0:
        raise StatusTransitionError()

    db.commit()
    logger.info('order_id %s status transited to %s and saved to database', order.id, new_status)

    return order



def process_order_payment(db, cache, order_id, customer_id, idempotency_key):
    order = get_customer_order(
        db,
        order_id=order_id,
        customer_id=customer_id
    )
    if not order:
        raise OrderNotFoundError()

    key = f'{order.id}:{customer_id}:{idempotency_key}'

    try:
        cached_response = get_from_cache(cache, key)
        if cached_response:
            logger.info(
                'hit idempotency key for order_id %s customer_id %s, idempotency_key %s',
                order_id, customer_id, idempotency_key)
            return OrderResponse.model_validate(json.loads(cached_response))

    except CacheError as error:
        logger.error('redis failed while checking idempotency_key for payment customer_id %s order_id %s idempotency_key %s',
                       customer_id, order.id, idempotency_key, exc_info=error)

    result = order_payment_status_transition(db, order)
    if result == 0:
        raise StatusTransitionError()

    db.commit()
    logger.info('customer_id %s order_id %s payment processed and saved to database',customer_id, order.id)

    response = OrderResponse.model_validate(order)
    json_response = OrderResponse.model_dump_json(response)

    try:
        set_cache_response(cache, key=key, value=json_response)
        logger.info(
            'customer_id %s order_id %s idempotency_key %s payment process saved to cache database',
            customer_id, order.id, idempotency_key
                )
    except CacheError as error:
        logger.error(
            'redis connection failed while setting key for payment customer_id %s order_id %s idempotency_key %s',
            customer_id, order_id, idempotency_key, exc_info=error
        )

    return response



