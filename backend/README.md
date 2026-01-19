# Mini-RAG Backend

FastAPI backend for the Mini-RAG system with Supabase pgvector, Gemini embeddings, Jina reranking, and citation-aware generation.

## Tech Stack

- **Framework**: FastAPI (Python 3.10+)
- **Vector Database**: Supabase with pgvector extension
- **Embeddings**: Google Gemini `text-embedding-004`
- **Reranker**: Jina Reranker API
- **LLM**: Gemini 2.5 Flash

## Architecture

```
app/
├── main.py              # FastAPI app entry point
├── config.py            # Settings & environment variables
├── dependencies.py      # Dependency injection
├── api/
│   ├── ingest.py        # POST /api/ingest - chunk & embed text
│   └── query.py         # POST /api/query - retrieve & generate
├── core/
│   ├── chunking.py      # Text chunking (1000 tokens, 120 overlap)
│   ├── embeddings.py    # Gemini embedding API
│   ├── retriever.py     # pgvector cosine similarity (top-8)
│   ├── reranker.py      # Jina reranker (top-3)
│   └── generator.py     # Gemini answer generation with citations
├── db/
│   ├── schema.sql       # Supabase schema & RPC function
│   └── supabase.py      # Supabase client
├── models/
│   ├── ingest.py        # Request/response models for ingest
│   └── query.py         # Request/response models for query
└── utils/
    ├── citations.py     # Citation list builder
    ├── timing.py        # Performance timing context manager
    └── token_estimator.py  # Token estimation utility
```

## Setup

### 1. Prerequisites

- Python 3.10+
- Supabase account (free tier)
- Google AI API key (Gemini)
- Jina API key

### 2. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_TABLE=documents

GEMINI_API_KEY=your-gemini-api-key
GEMINI_EMBEDDING_MODEL=text-embedding-004
GEMINI_CHAT_MODEL=gemini-1.5-flash

JINA_API_KEY=your-jina-api-key
JINA_RERANK_MODEL=jina-reranker-v2-base-multilingual

CHUNK_SIZE=1000
CHUNK_OVERLAP=120
RETRIEVAL_TOP_K=8
RERANK_TOP_K=3
```

### 4. Database Setup

Run `db/schema.sql` in Supabase SQL Editor to create:
- `documents` table with `vector(768)` embedding column
- `match_documents()` RPC function for similarity search

### 5. Run Development Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs: `http://localhost:8000/docs`

## API Endpoints

### POST /api/ingest

Chunk text, generate embeddings, store in Supabase.

**Request:**
```json
{
  "text": "Your text content...",
  "source": "user"
}
```

**Response:**
```json
{
  "chunks_inserted": 5,
  "token_estimate": 1200,
  "timings": {
    "chunking_ms": 2.5,
    "embedding_ms": 450.0,
    "insert_ms": 120.0
  }
}
```

### POST /api/query

Retrieve, rerank, and generate answer with citations.

**Request:**
```json
{
  "query": "Who led the first expedition around the world?"
}
```

**Response:**
```json
{
  "answer": "Ferdinand Magellan led the first expedition to sail around the world [1].",
  "citations": [
    {
      "id": 1,
      "source": "user",
      "chunk_id": "abc-123",
      "chunk_position": 0
    }
  ],
  "timings": {
    "embedding_ms": 400.0,
    "retrieval_ms": 150.0,
    "rerank_ms": 200.0,
    "generation_ms": 800.0
  },
  "token_estimate": 250,
  "retrieved_chunks": [...]
}
```

## RAG Pipeline

1. **Chunking**: Split text into ~1000 token chunks with 120 token overlap
2. **Embedding**: Generate 768-dim vectors using Gemini `text-embedding-004`
3. **Storage**: Insert chunks + embeddings into Supabase pgvector
4. **Retrieval**: Cosine similarity search (top-8 chunks)
5. **Reranking**: Jina reranker reduces to top-3 most relevant
6. **Generation**: Gemini 1.5 Flash generates grounded answer with inline citations `[1][2]`

## Testing

```bash
pytest -q
```

## Docker

```bash
docker build -t mini-rag-backend .
docker run --env-file .env -p 8000:8000 mini-rag-backend
```

## Deployment

Deploy to:
- **Render** (free tier)
- **Railway** (free tier)
- **Fly.io**

Set environment variables in platform dashboard.

## Design Decisions

- **No LangChain**: Clean, minimal abstractions for transparency
- **Client-side similarity fallback**: If RPC fails, compute cosine similarity in Python
- **Logging**: INFO-level logs for embedding dimensions, retrieval counts
- **Strict citations**: Gemini prompted to cite sources or return "I don't know"

## Limitations

- **Embedding dimension**: Fixed at 768 (Gemini `text-embedding-004`)
- **Chunking**: Simple word-based splitting (no semantic chunking)
- **Context window**: Limited to top-3 reranked chunks
- **Fallback retrieval**: Fetches all docs if RPC fails (inefficient at scale)

## Future Improvements

- Semantic chunking with sentence boundaries
- Hybrid search (keyword + vector)
- Streaming responses
- Caching for repeated queries
- Batch processing for large ingests
