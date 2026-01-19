from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
	query: str = Field(..., min_length=1)


class QueryResponse(BaseModel):
	answer: str
	citations: list[dict]
	timings: dict[str, float]
	token_estimate: int
	retrieved_chunks: list[dict]
