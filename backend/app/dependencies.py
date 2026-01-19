from collections.abc import AsyncGenerator
import httpx
from fastapi import Depends
from app.config import Settings, get_settings
from app.db.supabase import create_supabase_client

def settings_dependency() -> Settings:
	return get_settings()

def supabase_dependency(settings: Settings = Depends(settings_dependency)):
	return create_supabase_client(settings)

async def http_client_dependency(
	settings: Settings = Depends(settings_dependency),
) -> AsyncGenerator[httpx.AsyncClient, None]:
	timeout = httpx.Timeout(settings.request_timeout_seconds)
	async with httpx.AsyncClient(timeout=timeout) as client:
		yield client