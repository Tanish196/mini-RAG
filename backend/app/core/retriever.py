import json
import logging

from app.config import Settings

logger = logging.getLogger(__name__)

def retrieve_chunks(
    supabase,
    settings: Settings,
    query_embedding: list[float],
) -> list[dict]:
    # Use raw SQL query via supabase.postgrest instead of RPC
    # This bypasses RPC parameter issues with vector types
    embedding_array = "[" + ",".join(str(x) for x in query_embedding) + "]"
    
    try:
        # Try RPC first with the array format
        response = supabase.rpc(
            "match_documents",
            {
                "query_embedding": embedding_array,
                "match_count": settings.retrieval_top_k,
                "min_similarity": -1.0,
            }
        ).execute()
        
        results = getattr(response, "data", None) or []
        logger.info(f"Retrieved {len(results)} chunks via RPC")
        
        if results:
            return results
            
    except Exception as e:
        logger.warning(f"RPC failed: {e}, falling back to direct query")
    
    # Fallback: direct query without RPC
    # Get all documents and compute similarity in Python
    logger.info("Using fallback: fetching all documents for client-side similarity")
    response = supabase.table(settings.supabase_table).select("*").execute()
    
    all_docs = getattr(response, "data", None) or []
    logger.info(f"Fetched {len(all_docs)} total documents")
    
    if not all_docs:
        return []
    
    # Compute cosine similarity in Python
    import math
    
    def cosine_similarity(vec1, vec2):
        dot = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot / (mag1 * mag2)
    
    scored = []
    for doc in all_docs:
        emb = doc.get("embedding")
        if emb:
            # Supabase returns vector as string like "[0.1, 0.2, ...]", parse it
            if isinstance(emb, str):
                emb = json.loads(emb)
            
            sim = cosine_similarity(query_embedding, emb)
            scored.append({
                "id": doc.get("id"),
                "source": doc.get("source"),
                "chunk_id": doc.get("chunk_id"),
                "chunk_position": doc.get("chunk_position"),
                "content": doc.get("content"),
                "similarity": sim,
            })
    
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    results = scored[:settings.retrieval_top_k]
    logger.info(f"Retrieved {len(results)} chunks via fallback")
    return results