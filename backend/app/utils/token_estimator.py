import math


def estimate_tokens(text: str) -> int:
	if not text:
		return 0
	return max(1, math.ceil(len(text) / 4))


def estimate_tokens_for_texts(texts: list[str]) -> int:
	return sum(estimate_tokens(text) for text in texts)
