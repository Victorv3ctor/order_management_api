import pytest
from services.order import valid_order_status_transition
from exceptions import StatusTransitionError

@pytest.mark.parametrize("order_status, payload_status, result", [
    ('pending', 'paid', 'paid'),
    ('pending', 'cancelled', 'cancelled'),
    ('paid', 'processing', 'processing'),
    ('paid', 'cancelled', 'cancelled'),
    ('processing', 'shipped', 'shipped'),
    ('shipped', 'completed', 'completed'),
])

def test_status_transition_happy_path(order_status, payload_status, result):
    assert valid_order_status_transition(order_status, payload_status) == result


def test_status_transition_allowed_statuses_is_none():
    order_status = 'cancelled'
    new_status = 'paid'

    with pytest.raises(StatusTransitionError):
        valid_order_status_transition(order_status, new_status)

def test_status_transition_new_status_not_in_allowed():
    order_status='pending'
    new_status='shipped'

    with pytest.raises(StatusTransitionError):
        valid_order_status_transition(order_status, new_status)


