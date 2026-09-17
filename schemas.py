from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
import datetime

"""TOKEN"""
class TokenResponse(BaseModel):
    access_token: str
    token_type: str


"""CUSTOMER"""
class CustomerCreate(BaseModel):
    email: str
    password: str

class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str


class CustomerDetailedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str


class CustomersResponse(BaseModel):
    customers: list[CustomerDetailedResponse]


"""PRODUCT"""
class ProductCreate(BaseModel):
    name: str
    price: int
    stock_quantity: int

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: int
    stock_quantity: int

"""ORDER ITEM"""

class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    qty: int

class OrderItemCreate(BaseModel):
    product_id: int
    qty: int = Field(gt=0)


"""ORDER"""
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

"""PAGINATION"""
class PaginatedOrderResponse(BaseModel):
    items: list[OrderResponse]
    page: int
    page_size: int
    total_count: int
    has_next_page: bool
    has_previous_page: bool

class PaginatedProductsResponse(BaseModel):
    items: list[ProductResponse]
    page: int
    page_size: int
    total_count: int
    has_next_page: bool
    has_previous_page: bool



