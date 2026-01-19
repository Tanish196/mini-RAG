import httpx
from app.config import Settings

async def rerank_chunks(
	query: str,
	chunks: list[dict],
	settings: Settings,
	http_client: httpx.AsyncClient,
) -> list[dict]:
	if not chunks:
		return []

	url = "https://api.jina.ai/v1/rerank"
	payload = {
		"model": settings.jina_rerank_model,
		"query": query,
		"top_n": settings.rerank_top_k,
		"documents": [
			{"id": str(index), "text": chunk["content"]}
			for index, chunk in enumerate(chunks)
		],
	}
	headers = {"Authorization": f"Bearer {settings.jina_api_key}"}
	response = await http_client.post(url, json=payload, headers=headers)
	response.raise_for_status()
	data = response.json()

	results = data.get("results", [])
	reranked = []
	for item in results:
		original_index = int(item["index"])
		chunk = chunks[original_index].copy()
		chunk["rerank_score"] = item.get("relevance_score")
		reranked.append(chunk)

	return reranked