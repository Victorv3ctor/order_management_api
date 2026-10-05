import pytest
from schemas.order import OrderCreate, OrderItemCreate

def test_order_create_without_items():
    with pytest.raises(ValueError):
        OrderCreate(
            items = []
        )

def test_order_with_items():
    order_payload=OrderCreate(
        items=[
            OrderItemCreate(product_id=1, qty=1)
        ]
    )
    assert len(order_payload.items) == 1
    assert order_payload.items[0].product_id==1
    assert order_payload.items[0].qty == 1


