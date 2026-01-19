def build_citation_list(chunks: list[dict]) -> list[dict]:
	return [
		{
			"id": index + 1,
			"source": chunk.get("source"),
			"chunk_id": chunk.get("chunk_id"),
			"chunk_position": chunk.get("chunk_position"),
		}
		for index, chunk in enumerate(chunks)
	]
