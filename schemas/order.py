from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
import datetime

class OrderItemCreate(BaseModel):
    product_id: int
    qty: int = Field(gt=0)


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    qty: int


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderStatusUpdate(BaseModel):
    status: Literal["paid", "processing", "shipped", "completed", "cancelled"]


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    total_amount: int
    status: str
    created_at: datetime.datetime
    order_items: list[OrderItemResponse]


class PaginatedOrderResponse(BaseModel):
    items: list[OrderResponse]
    page: int
    page_size: int
    total_count: int
    has_next_page: bool
    has_previous_page: bool
