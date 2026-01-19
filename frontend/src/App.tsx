import { useState } from 'react';
import './App.css';
import { ingestText, queryText, type QueryResponse } from './api';

function App() {
  const [contextText, setContextText] = useState('');
  const [query, setQuery] = useState('');
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [isIngesting, setIsIngesting] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);
  const [ingestStatus, setIngestStatus] = useState('');
  const [error, setError] = useState('');

  const handleIngest = async () => {
    if (!contextText.trim()) {
      setError('Please enter text to ingest');
      return;
    }

    setIsIngesting(true);
    setError('');
    setIngestStatus('');

    try {
      const result = await ingestText({ text: contextText, source: 'user' });
      setIngestStatus(
        `✓ Ingested ${result.chunks_inserted} chunks (${result.token_estimate} tokens)`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ingest failed');
    } finally {
      setIsIngesting(false);
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    setIsQuerying(true);
    setError('');
    setQueryResult(null);

    try {
      const result = await queryText({ query });
      setQueryResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Query failed');
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Mini-RAG System</h1>
        <p>Retrieval-Augmented Generation with Citations</p>
      </header>

      <div className="container">
        {/* Ingest Section */}
        <section className="section">
          <h2>1. Ingest Text</h2>
          <textarea
            className="textarea"
            placeholder="Paste your text here to ingest into the knowledge base..."
            value={contextText}
            onChange={(e) => setContextText(e.target.value)}
            rows={8}
          />
          <button
            className="btn btn-primary"
            onClick={handleIngest}
            disabled={isIngesting}
          >
            {isIngesting ? 'Ingesting...' : 'Ingest Text'}
          </button>
          {ingestStatus && <p className="status success">{ingestStatus}</p>}
        </section>

        {/* Query Section */}
        <section className="section">
          <h2>2. Query</h2>
          <input
            className="input"
            type="text"
            placeholder="Ask a question..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
          />
          <button
            className="btn btn-success"
            onClick={handleQuery}
            disabled={isQuerying}
          >
            {isQuerying ? 'Searching...' : 'Search'}
          </button>
        </section>

        {/* Error Display */}
        {error && <p className="status error">{error}</p>}

        {/* Answer Section */}
        {queryResult && (
          <section className="section answer-section">
            <h2>Answer</h2>
            <div className="answer-box">
              <p className="answer-text">{queryResult.answer}</p>
            </div>

            {queryResult.citations.length > 0 && (
              <div className="citations">
                <h3>Citations</h3>
                <ul>
                  {queryResult.citations.map((citation) => (
                    <li key={citation.id}>
                      [{citation.id}] {citation.source} (chunk {citation.chunk_position})
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="metrics">
              <h3>Metrics</h3>
              <div className="metrics-grid">
                <div className="metric">
                  <span className="metric-label">Embedding:</span>
                  <span className="metric-value">
                    {queryResult.timings.embedding_ms?.toFixed(0)}ms
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Retrieval:</span>
                  <span className="metric-value">
                    {queryResult.timings.retrieval_ms?.toFixed(0)}ms
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Rerank:</span>
                  <span className="metric-value">
                    {queryResult.timings.rerank_ms?.toFixed(0)}ms
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Generation:</span>
                  <span className="metric-value">
                    {queryResult.timings.generation_ms?.toFixed(0)}ms
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Tokens:</span>
                  <span className="metric-value">{queryResult.token_estimate}</span>
                </div>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

export default App;

