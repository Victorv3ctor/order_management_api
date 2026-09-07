import pytest
from service import valid_status_transition

#Valid / invalid transitions
@pytest.mark.parametrize("order_status, payload_status, result", [
    ('pending', 'paid', 'paid'),
    ('pending', 'cancelled', 'cancelled'),
    ('paid', 'processing', 'processing'),
    ('paid', 'cancelled', 'cancelled'),
    ('processing', 'shipped', 'shipped'),
    ('shipped', 'completed', 'completed'),
    ('cancelled', 'pending', None),
    ('pending', 'processing', None),
    ('completed', 'cancelled', None),
    ('processing', 'cancelled', None),
    (None, 'paid', None)
])

def test_status_transition(order_status, payload_status, result):
    assert valid_status_transition(order_status, payload_status) == result


