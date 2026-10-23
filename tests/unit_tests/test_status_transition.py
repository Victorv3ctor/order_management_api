import pytest
from app.services.order import allowed_statuses_to_change_for_new_status



@pytest.mark.parametrize("new_status, allowing_statuses", [
    ('paid', ['pending']),
    ('cancelled', ['pending', 'paid']),
    ('processing', ['paid']),
    ('shipped', ['processing']),
    ('completed', ['shipped']),
])

def test_status_transition(new_status, allowing_statuses):
    assert allowed_statuses_to_change_for_new_status(new_status) == allowing_statuses



