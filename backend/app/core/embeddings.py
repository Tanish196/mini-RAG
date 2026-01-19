import logging

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


async def embed_texts(texts: list[str], settings: Settings, http_client: httpx.AsyncClient) -> list[list[float]]:
	if not texts:
		return []

	model_name = settings.gemini_embedding_model
	if not model_name.startswith("models/"):
		model_name = f"models/{model_name}"

	url = (
		f"https://generativelanguage.googleapis.com/v1beta/"
		f"{model_name}:batchEmbedContents?key={settings.gemini_api_key}"
	)
	payload = {
		"requests": [
			{"model": model_name, "content": {"parts": [{"text": text}]}}
			for text in texts
		]
	}
	response = await http_client.post(url, json=payload)
	response.raise_for_status()
	data = response.json()

	embeddings = [item["values"] for item in data.get("embeddings", [])]
	if len(embeddings) != len(texts):
		raise RuntimeError("Embedding response count does not match input count.")
	
	if embeddings:
		logger.info(f"Generated {len(embeddings)} embeddings, dimension={len(embeddings[0])}")
	
	return embeddings