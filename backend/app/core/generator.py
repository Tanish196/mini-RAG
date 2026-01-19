import httpx
from app.config import Settings

async def generate_answer(
	query: str,
	chunks: list[dict],
	settings: Settings,
	http_client: httpx.AsyncClient,
) -> str:
	if not chunks:
		return "I don't know based on the provided text."

	context_blocks = []
	for idx, chunk in enumerate(chunks, start=1):
		context_blocks.append(f"[{idx}] {chunk['content']}")

	context_text = "\n\n".join(context_blocks)
	system_prompt = (
		"You are a grounded assistant. Answer only using the provided context. "
		"If the answer is not in the context, respond exactly with: "
		"I don't know based on the provided text."
	)
	user_prompt = (
		f"Question: {query}\n\n"
		f"Context:\n{context_text}\n\n"
		"Provide a concise answer with inline citations like [1] or [1][2]."
	)

	url = (
		f"https://generativelanguage.googleapis.com/v1beta/models/"
		f"{settings.gemini_chat_model}:generateContent?key={settings.gemini_api_key}"
	)
	payload = {
		"contents": [
			{"role": "user", "parts": [{"text": system_prompt}]},
			{"role": "user", "parts": [{"text": user_prompt}]},
		],
		"generationConfig": {
			"temperature": 0.2,
			"maxOutputTokens": 512,
		},
	}

	response = await http_client.post(url, json=payload)
	response.raise_for_status()
	data = response.json()
	candidates = data.get("candidates", [])
	if not candidates:
		return "I don't know based on the provided text."

	text_parts = candidates[0].get("content", {}).get("parts", [])
	answer = "".join(part.get("text", "") for part in text_parts).strip()

	if not answer:
		return "I don't know based on the provided text."
	if "I don't know based on the provided text" in answer:
		return "I don't know based on the provided text."

	return answer