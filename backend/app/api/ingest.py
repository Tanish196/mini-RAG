import logging

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings
from app.core.chunking import chunk_text
from app.core.embeddings import embed_texts
from app.dependencies import http_client_dependency, settings_dependency, supabase_dependency
from app.models.ingest import IngestRequest, IngestResponse
from app.utils.timing import time_block
from app.utils.token_estimator import estimate_tokens_for_texts

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ingest"])

@router.post("/ingest", response_model=IngestResponse)
async def ingest_text(
	payload: IngestRequest,
	settings: Settings = Depends(settings_dependency),
	supabase=Depends(supabase_dependency),
	http_client=Depends(http_client_dependency),
):
	if not payload.text.strip():
		raise HTTPException(status_code=400, detail="Text is required.")

	with time_block() as chunk_timer:
		chunks = chunk_text(payload.text, settings.chunk_size, settings.chunk_overlap)
	logger.info(f"Created {len(chunks)} chunks from text")

	with time_block() as embed_timer:
		embeddings = await embed_texts(
			[chunk["text"] for chunk in chunks],
			settings=settings,
			http_client=http_client,
		)

	rows = []
	for chunk, embedding in zip(chunks, embeddings, strict=True):
		rows.append(
			{
				"source": payload.source,
				"chunk_id": chunk["chunk_id"],
				"chunk_position": chunk["chunk_position"],
				"content": chunk["text"],
				"embedding": embedding,
			}
		)

	logger.info(f"Inserting {len(rows)} rows into Supabase table '{settings.supabase_table}'")
	with time_block() as insert_timer:
		result = supabase.table(settings.supabase_table).insert(rows).execute()

	insert_error = getattr(result, "error", None)
	if insert_error:
		logger.error(f"Insert failed: {getattr(insert_error, 'message', str(insert_error))}")
		raise HTTPException(status_code=500, detail=getattr(insert_error, "message", str(insert_error)))
	if getattr(result, "data", None) is None:
		logger.error("Insert returned no data")
		raise HTTPException(status_code=500, detail="Failed to insert chunks into Supabase.")

	logger.info(f"Successfully inserted {len(rows)} chunks into database")

	token_estimate = estimate_tokens_for_texts([payload.text])
	return IngestResponse(
		chunks_inserted=len(rows),
		token_estimate=token_estimate,
		timings={
			"chunking_ms": chunk_timer.elapsed_ms,
			"embedding_ms": embed_timer.elapsed_ms,
			"insert_ms": insert_timer.elapsed_ms,
		},
	)