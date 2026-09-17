def valid_status_transition(order_status, payload_status):
    order_status_mapper = {
        'pending': ['paid', 'cancelled'],
        'paid': ['processing', 'cancelled'],
        'processing': ['shipped'],
        'shipped': ['completed']
    }
    allowed_statuses = order_status_mapper.get(order_status, None)

    if allowed_statuses is None or payload_status not in allowed_statuses:
        return None

    return payload_status


def total_price_calculation(products_by_id, payload_items):
    return sum(
        [
            products_by_id[payload_item.product_id].price * payload_item.qty for payload_item in payload_items
         ]
    )


