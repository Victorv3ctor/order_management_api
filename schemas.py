from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

"""CUSTOMER"""
class CustomerCreate(BaseModel):
    #nie ma id, bo klient nie  podaje id przy tworzeniu
    name: str
    email: str

    # orders: list[OrderResponse] #deklarujesz ze orders, to lista obiektow Order,
    # a order ma juz swoj response, logiczne


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    #^ wolno ci czytac dane z atrybutow obiektu
    #(customer.id, customer.name, customer.email),
    # bo my zwracamy z endpointa obiekt sql alchemy

    id: int
    name: str
    email: str

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
    qty: int = Field(gt=0) #greater than 0, ta wartosc musi byc wieksze od 0 (wejscie)


"""ORDER"""
class OrderCreate(BaseModel):
    customer_id: int
    items: list[OrderItemCreate] = Field(min_length=1)

class OrderStatusUpdate(BaseModel):
    status: Literal["paid", "processing", "shipped", "completed", "cancelled"]


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    status: str
    total_amount: int
    order_items: list[OrderItemResponse]




