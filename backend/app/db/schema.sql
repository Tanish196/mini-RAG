create extension if not exists vector;
create extension if not exists pgcrypto;

create table if not exists documents (
	id uuid primary key default gen_random_uuid(),
	source text not null,
	chunk_id text not null,
	chunk_position integer not null,
	content text not null,
	embedding vector(768) not null,
	created_at timestamptz not null default now()
);

create index if not exists documents_embedding_idx
	on documents using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create or replace function match_documents(
	query_embedding vector(768),
	match_count int,
	min_similarity float
)
returns table (
	id uuid,
	source text,
	chunk_id text,
	chunk_position integer,
	content text,
	similarity float
)
language sql stable as $$
	select
		id,
		source,
		chunk_id,
		chunk_position,
		content,
		1 - (embedding <=> query_embedding) as similarity
	from documents
	where 1 - (embedding <=> query_embedding) >= min_similarity
	order by embedding <=> query_embedding
	limit match_count;
$$;