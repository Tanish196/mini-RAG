from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.core.chunking import chunk_text
from app.utils.citations import build_citation_list


def test_chunking_overlap():
    text = " ".join([f"token{i}" for i in range(0, 2500)])
    chunks = chunk_text(text, chunk_size=1000, overlap=120)

    assert len(chunks) >= 2
    assert chunks[0]["chunk_position"] == 0
    assert chunks[1]["chunk_position"] == 1

    first_tokens = chunks[0]["text"].split()
    second_tokens = chunks[1]["text"].split()
    assert first_tokens[-120:] == second_tokens[:120]


def test_citation_list():
    chunks = [
        {"source": "user", "chunk_id": "c1", "chunk_position": 0},
        {"source": "user", "chunk_id": "c2", "chunk_position": 1},
    ]
    citations = build_citation_list(chunks)

    assert citations[0]["id"] == 1
    assert citations[1]["id"] == 2
    assert citations[0]["chunk_id"] == "c1"
