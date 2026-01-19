import { API_BASE_URL } from './config';

export interface IngestRequest {
  text: string;
  source?: string;
}

export interface IngestResponse {
  chunks_inserted: number;
  token_estimate: number;
  timings: Record<string, number>;
}

export interface QueryRequest {
  query: string;
}

export interface Citation {
  id: number;
  source: string;
  chunk_id: string;
  chunk_position: number;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  timings: Record<string, number>;
  token_estimate: number;
  retrieved_chunks: any[];
}

export async function ingestText(request: IngestRequest): Promise<IngestResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Ingest failed');
  }

  return response.json();
}

export async function queryText(request: QueryRequest): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Query failed');
  }

  return response.json();
}
