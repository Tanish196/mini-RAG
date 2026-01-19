from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
	model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

	app_name: str = "mini-rag-backend"
	environment: str = "dev"

	supabase_url: str
	supabase_service_role_key: str
	supabase_table: str = "documents"

	gemini_api_key: str
	gemini_embedding_model: str = "text-embedding-004"
	gemini_chat_model: str = "gemini-1.5-flash"

	jina_api_key: str
	jina_rerank_model: str = "jina-reranker-v2-base-multilingual"

	chunk_size: int = 1000
	chunk_overlap: int = 120
	retrieval_top_k: int = 8
	rerank_top_k: int = 3

	request_timeout_seconds: float = 30.0


@lru_cache
def get_settings() -> Settings:
	return Settings()