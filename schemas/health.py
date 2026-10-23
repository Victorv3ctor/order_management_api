from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database_health: bool
    cache_health: bool

