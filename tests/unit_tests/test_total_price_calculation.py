import pytest
from service import total_price_calculation
from types import SimpleNamespace


@pytest.fixture
def products_by_id():
    products = [
        SimpleNamespace(id=1, price=100),
        SimpleNamespace(id=2, price=100)
    ]

    return {product.id: product for product in products}



def test_total_price_calculation(products_by_id, payload_items):
    assert total_price_calculation(products_by_id, payload_items) == 200

def test_total_price_calculation_empty_order_items(products_by_id):
    assert total_price_calculation(products_by_id, []) == 0






