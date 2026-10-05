from pydantic import BaseModel, ConfigDict

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


class PaginatedProductsResponse(BaseModel):
    items: list[ProductResponse]
    page: int
    page_size: int
    total_count: int
    has_next_page: bool
    has_previous_page: bool
