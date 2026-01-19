from fastapi import APIRouter, Depends
from app.config import Settings
from app.core.embeddings import embed_texts
from app.core.generator import generate_answer
from app.core.reranker import rerank_chunks
from app.core.retriever import retrieve_chunks
from app.dependencies import http_client_dependency, settings_dependency, supabase_dependency
from app.models.query import QueryRequest, QueryResponse
from app.utils.citations import build_citation_list
from app.utils.timing import time_block
from app.utils.token_estimator import estimate_tokens_for_texts


router = APIRouter(tags=["query"])

@router.post("/query", response_model=QueryResponse)
async def query_text(
	payload: QueryRequest,
	settings: Settings = Depends(settings_dependency),
	supabase=Depends(supabase_dependency),
	http_client=Depends(http_client_dependency),
):
	with time_block() as embed_timer:
		query_embedding = (await embed_texts([payload.query], settings, http_client))[0]

	with time_block() as retrieve_timer:
		retrieved = retrieve_chunks(
			supabase,
			settings=settings,
			query_embedding=query_embedding,
		)

	if not retrieved:
		return QueryResponse(
			answer="I don't know based on the provided text.",
			citations=[],
			timings={
				"embedding_ms": embed_timer.elapsed_ms,
				"retrieval_ms": retrieve_timer.elapsed_ms,
				"rerank_ms": 0.0,
				"generation_ms": 0.0,
			},
			token_estimate=estimate_tokens_for_texts([payload.query]),
			retrieved_chunks=[],
		)

	with time_block() as rerank_timer:
		reranked = await rerank_chunks(
			query=payload.query,
			chunks=retrieved,
			settings=settings,
			http_client=http_client,
		)

	with time_block() as generate_timer:
		answer = await generate_answer(
			query=payload.query,
			chunks=reranked,
			settings=settings,
			http_client=http_client,
		)

	citations = build_citation_list(reranked)
	token_estimate = estimate_tokens_for_texts(
		[payload.query] + [chunk["content"] for chunk in reranked]
	)

	return QueryResponse(
		answer=answer,
		citations=citations,
		timings={
			"embedding_ms": embed_timer.elapsed_ms,
			"retrieval_ms": retrieve_timer.elapsed_ms,
			"rerank_ms": rerank_timer.elapsed_ms,
			"generation_ms": generate_timer.elapsed_ms,
		},
		token_estimate=token_estimate,
		retrieved_chunks=reranked,
	)