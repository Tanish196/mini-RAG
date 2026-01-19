import math
import uuid

def chunk_text(text: str, chunk_size: int, overlap: int) -> list[dict]:
	tokens = text.split()
	if not tokens:
		return []

	step = max(chunk_size - overlap, 1)
	chunks = []
	for start in range(0, len(tokens), step):
		end = start + chunk_size
		token_slice = tokens[start:end]
		if not token_slice:
			break
		chunk_text_value = " ".join(token_slice)
		chunk_position = math.floor(start / step)
		chunks.append(
			{
				"chunk_id": str(uuid.uuid4()),
				"chunk_position": chunk_position,
				"text": chunk_text_value,
			}
		)

		if end >= len(tokens):
			break

	return chunks
