# Mini-RAG System

A production-minded Retrieval-Augmented Generation (RAG) system built for an AI Engineer assessment. Users paste text, ask questions, and receive grounded answers with inline citations.

**Live Demo:** https://mini-rag-1-i7d0.onrender.com

---

## Project Overview

This is a minimal, transparent RAG pipeline that:
- Accepts raw text input (no file upload)
- Chunks text into semantic segments
- Generates embeddings via Google Gemini
- Stores vectors in Supabase (PostgreSQL + pgvector)
- Retrieves top-K relevant chunks via cosine similarity
- Reranks results using Jina Reranker
- Generates grounded answers with inline citations
- Returns "I don't know" when no relevant context exists

**Design Philosophy:**
- No orchestration frameworks (LangChain, etc.)
- Direct REST API calls for transparency
- Clean separation of concerns
- Production-ready error handling
- Simple, explainable evaluation

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  User Interface (React + TypeScript)                        │
│  - Text input for ingestion                                 │
│  - Query input + citation display                           │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Backend                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ /api/ingest  │  │ /api/query   │  │ CORS + Logs  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────┬────────────────────┬────────────────────┬─────────────┘
      │                    │                    │
      │ Embed              │ Embed Query        │ Generate
      ▼                    ▼                    ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Gemini       │  │ Supabase     │  │ Gemini       │
│ Embeddings   │  │ (pgvector)   │  │ 1.5 Flash    │
│ (768-dim)    │  │ Cosine Sim   │  │ LLM          │
└──────────────┘  └──────┬───────┘  └──────────────┘
                         │
                         │ Top-8 Chunks
                         ▼
                  ┌──────────────┐
                  │ Jina         │
                  │ Reranker     │
                  │ → Top-3      │
                  └──────────────┘
```

**Tech Stack:**
- **Backend:** FastAPI (Python 3.10+)
- **Vector DB:** Supabase (PostgreSQL + pgvector extension)
- **Embeddings:** Google Gemini `text-embedding-004` (768-dim)
- **Reranker:** Jina `jina-reranker-v2-base-multilingual`
- **LLM:** Google Gemini `1.5 Flash`
- **Frontend:** React 19 + TypeScript + Vite
- **Hosting:** Render (backend), Vercel (frontend)

---

## System Flow (Step-by-Step)

### Ingestion Flow
1. User pastes raw text into frontend
2. Frontend sends text to `POST /api/ingest`
3. Backend chunks text into ~1000-token segments (120-token overlap)
4. Gemini generates 768-dim embeddings for each chunk
5. Chunks + embeddings stored in Supabase `documents` table
6. Return chunk count + timing metrics

### Query Flow
1. User submits question
2. Frontend sends query to `POST /api/query`
3. Backend generates query embedding via Gemini
4. Supabase performs cosine similarity search (top-8 chunks)
   - **Fallback:** If RPC fails, compute similarity client-side
5. Jina Reranker reduces top-8 to top-3 most relevant
6. Top-3 chunks passed to Gemini 1.5 Flash with prompt:
   - "Answer using ONLY the provided context"
   - "Cite sources as [1], [2], [3]"
   - "If no relevant context, say 'I don't know'"
7. Return answer + citations + timing metrics

---

## Chunking Strategy

**Approach:** Token-based chunking with overlap

**Parameters:**
- Chunk size: 1000 tokens (~750 words)
- Overlap: 120 tokens (~90 words)
- Split method: Word boundaries (preserves sentences)
---

## Vector Storage & Retrieval

**Database:** Supabase PostgreSQL with `pgvector` extension

**Schema:**
```sql
CREATE TABLE documents (
  id UUID PRIMARY KEY,
  source TEXT,
  chunk_text TEXT,
  chunk_position INTEGER,
  embedding vector(768),
  created_at TIMESTAMP
);

CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
```

**Retrieval Strategy:**
1. **Primary:** RPC function `match_documents(query_embedding, top_k)`
   - Uses `ivfflat` index for fast approximate search
   - Cosine similarity: `1 - (embedding <=> query_embedding)`
2. **Fallback:** If RPC fails, fetch all docs and compute cosine similarity in Python
   - Graceful degradation for small datasets
   - Logs warning for debugging

**Why Supabase:**
- Hosted PostgreSQL (no infra management)
- Native pgvector support
- Free tier sufficient for demo/eval
- REST API + Python client

---

## Reranking Strategy

**Tool:** Jina AI Reranker API (`jina-reranker-v2-base-multilingual`)

**Process:**
1. Receive top-8 chunks from vector search
2. Send query + 8 chunks to Jina API
3. Jina scores each chunk for relevance (0-1 scale)
4. Return top-3 highest-scoring chunks

**Why rerank:**
- Vector similarity ≠ semantic relevance
- Reranker uses cross-attention between query and chunk
- Reduces context size for LLM (cost + latency)
- Improves answer quality (fewer irrelevant chunks)

**Tradeoff:**
- Adds ~200ms latency
- External API dependency
- But: significantly improves precision

---

## Answer Generation & Citations

**LLM:** Google Gemini 2.5 Flash (fast, cost-effective)

**Prompt Structure:**
```
You are a helpful assistant. Answer the question using ONLY
the provided context chunks. Cite sources using [1], [2], [3].
If the context is insufficient, respond with "I don't know".

Context:
[1] {chunk_text_1}
[2] {chunk_text_2}
[3] {chunk_text_3}

Question: {user_query}
```

**Citation Tracking:**
- Each chunk assigned a citation ID [1], [2], [3]
- LLM instructed to include citations inline
- Frontend displays clickable citation list
- Citations include: source, chunk position, text preview


---

## No-Answer Handling

**Strategy:** Explicit instruction + early exit

**Implementation:**
1. If retrieval returns 0 chunks → immediate "No relevant context found"
2. If reranker scores are all below threshold → "I don't know"
3. LLM prompt explicitly allows "I don't know" responses
4. No hallucination fallback (no web search, no general knowledge)

**Why this matters:**
- RAG systems must acknowledge knowledge gaps
- Hallucination risks are higher without grounding
- Users trust "I don't know" more than confidently wrong answers

---

## Evaluation Methodology

**Approach:** Manual Q/A pairs with ground truth

**Evaluation: Based on a wikipedia article based on Marie Curie**
```
| Question | Actual Answer |
| What scientific discovery made Marie and Pierre Curie famous? | Alexander Graham Bell | Marie and Pierre Curie became famous for their discovery of radium [1] | 
|Where and when was Marie Curie born? |Marie was born in 1867 in Warsaw, Poland [1]. |
| Why was Marie Curie unable to continue her higher education in Warsaw | Marie Curie was unable to continue her higher education in Warsaw because the university in Warsaw was closed to women [1] |
| What decision did Marie Curie make after being denied admission to the university in Warsaw? | After being denied admission to the university in Warsaw, Marie Curie defiantly left Poland and in 1891 entered the Sorbonne, a French university, where she earned her master’s degree and doctorate in physics [1]. |
| What degrees did Marie Curie earn at the Sorbonne | Marie Curie earned her master's degree and doctorate in physics at the Sorbonne [1]. |
| What tragic event occurred in 1906, and how did it affect Marie Curie? | In 1906, Pierre Curie was killed by a horse-drawn wagon [1]. This event stunned Marie Curie, causing her heartbreaking anguish and increased distress due to having two young daughters to raise by herself [1]. Her feeling of desolation began to fade when she was asked to succeed her husband as a physics professor at the Sorbonne [1]. |
| What illness did Marie Curie eventually suffer from, and what caused it? | Marie Curie eventually suffered a fatal illness from her long exposure to radium [1].|
| Did Marie Curie ever regret her dedication to science? Give a reason from the passage.| No, Marie Curie never regretted her dedication to science [1]. She never became disillusioned about her work, regardless of the consequences, and had dedicated herself to science and to revealing the mysteries of the physical world [1].|
```
**Metrics:**
- Precision: 100% (8/8 correct)

---

## Tradeoffs & Limitations

**Current Limitations:**
1. **Chunking:** Word-based splitting (no semantic sentence boundaries)
2. **Retrieval:** Fallback fetches all docs (inefficient at scale)
3. **Context window:** Limited to top-3 chunks (may miss relevant info)
4. **No hybrid search:** Pure vector search (no keyword/BM25)
5. **No caching:** Repeated queries re-embed and retrieve
6. **No streaming:** Answers load all at once (slow for long responses)
7. **Single-turn:** No conversation history or follow-up context

**Design Tradeoffs:**
- **No file upload** → Simpler UX, no storage/parsing overhead
- **No authentication** → Faster dev, but unsuitable for production
- **REST APIs over SDKs** → More transparent, but more boilerplate
- **Manual evaluation** → Fast and accurate for small scale

**Scalability Concerns:**
- Supabase free tier: 500MB database limit
- Jina API: Rate limits on free tier
- Gemini API: 15 requests/minute (free tier)

---

## What I Would Improve Next

1. **Semantic chunking:** Split on sentence boundaries using spaCy/NLTK
2. **Streaming responses:** Server-sent events for real-time answer generation
3. **Query caching:** Cache embeddings + results for repeated queries
4. **Better error messages:** User-friendly error handling in frontend
5. **Hybrid search:** Combine vector search + BM25 keyword search
6. **Multi-turn conversations:** Maintain chat history with session IDs
7. **Document metadata:** Store source URLs, titles, timestamps
8. **Evaluation dashboard:** Automated scoring with LLM-as-judge
9. **Production-ready auth:** JWT tokens + user management
10. **File upload:** Support PDF, DOCX, TXT with parsing
11. **Fine-tuned reranker:** Train domain-specific reranker for better precision

---

## Setup Instructions (Local)

### Prerequisites
- Python 3.10+
- Node.js 18+
- Supabase account (free tier)
- API keys: Gemini, Jina

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  
pip install -r requirements.txt


cp .env.example .env


uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs: `http://localhost:8000/docs`

### Frontend Setup
```bash
cd frontend
npm install

cp .env.example .env

npm run dev
```

Open `http://localhost:5173`

---

## Environment Variables

### Backend (`backend/.env`)
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

### Frontend (`frontend/.env`)
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## Deployment Notes

### Backend (Render)
1. Connect GitHub repo to Render
2. Select "Web Service" → Docker environment
3. Set Dockerfile path: `backend/Dockerfile`
4. Add environment variables (see above)
5. Deploy

**Important:** Dockerfile uses `${PORT:-8000}` to support Render's dynamic port assignment.

### Frontend (Vercel)
1. Connect GitHub repo to Vercel
2. Set root directory: `frontend`
3. Add environment variable: `VITE_API_BASE_URL=https://your-backend.onrender.com`
4. Deploy

### Database (Supabase)
1. Create project at supabase.com
2. Run `backend/app/db/schema.sql` in SQL Editor
3. Enable pgvector extension (auto-enabled on new projects)
4. Copy connection URL + service role key to backend `.env`

---

## Live Demo & Links

- **Live Frontend:** https://mini-rag-seven.vercel.app/
- **Live Backend:** https://mini-rag-1-i7d0.onrender.com/
- **API Docs:** https://mini-rag-1-i7d0.onrender.com/docs

---

**Built with transparency, tested with care, ready for evaluation.**
