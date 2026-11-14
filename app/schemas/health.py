from pydantic import BaseModel


class DatabaseCounts(BaseModel):
    investigations: int
    test_rows: int
    habitats: int
    documents: int
    pages: int
    chunks: int
    chunks_embedded: int


class HealthResponse(BaseModel):
    status: str
    database: DatabaseCounts
