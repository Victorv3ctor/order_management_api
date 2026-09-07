import pytest
from schemas import OrderCreate
from schemas import OrderItemCreate

def test_order_without_items():
    with pytest.raises(ValueError):
        OrderCreate(
            customer_id=1,
            items = []
        )

def test_order_with_items():
    order =  OrderCreate(
        customer_id=1, items=[
            OrderItemCreate(product_id=1, qty=1)
        ]
    )
    assert order.customer_id == 1
    assert len(order.items) == 1


