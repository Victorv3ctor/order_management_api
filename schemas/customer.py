from pydantic import BaseModel, ConfigDict

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


class CustomersInfoResponse(BaseModel):
    customers: list[CustomerDetailedResponse]