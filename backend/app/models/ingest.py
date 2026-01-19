from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
	text: str = Field(..., min_length=1)
	source: str = Field("user")


class IngestResponse(BaseModel):
	chunks_inserted: int
	token_estimate: int
	timings: dict[str, float]
