-- FlameScope database schema (PostgreSQL 14+ with the pgvector extension).
-- Safe to run again: everything is "if not exists".

create extension if not exists vector;         -- vector search for RAG, inside the same database

-- One row per NASA PSI investigation. The full card (summary, findings, limitations, sources) is kept as JSON.
create table if not exists investigations (
    id              text primary key,          -- 'PSI-25'
    name            text not null,             -- 'BASS-II'
    title           text,
    in_space        boolean,
    fuel_type       text,                      -- solid | droplet | gas | smoke | ground
    hardware_group  text,
    safety_jobs     text[],                    -- prevention / detection / suppression
    card            jsonb not null             -- the whole card from data/psi/cards.json
);

-- One row per cleaned test row (data/psi/clean/*.csv). Columns shared by all tables are real columns;
-- columns specific to one table are kept in "extra".
create table if not exists tests (
    id                bigserial primary key,
    psi_id            text not null references investigations(id),
    clean_file        text not null,           -- 'bass2.csv'
    investigation     text,
    test_id           text,
    test_date         text,
    row_granularity   text,                    -- test | test_day | planned_range ...
    n_tests           integer,                 -- null = number of fires unknown
    fuel              text,
    fuel_type         text,
    o2_pct            real,
    o2_min_pct        real,
    o2_max_pct        real,
    o2_location       text,                    -- chamber | burner_stream (never compare the two)
    o2_assumed        boolean,
    pressure_kpa      real,
    pressure_min_kpa  real,
    pressure_max_kpa  real,
    pressure_assumed  boolean,
    flow_cm_s         real,
    flow_min_cm_s     real,
    flow_max_cm_s     real,
    n2_pct            real,
    co2_pct           real,
    he_pct            real,
    diluent           text,
    o2_partial_kpa    real,
    lunar_air         boolean,
    gravity           text,
    has_result        boolean,
    flags             text[],
    source_file       text,                    -- original NASA table
    source_row        integer,
    extra             jsonb                    -- table-specific columns
);
create index if not exists tests_psi on tests (psi_id);
create index if not exists tests_conditions on tests (o2_location, o2_pct, pressure_kpa);

-- Habitat atmospheres (content/habitats.json), with their sources.
create table if not exists habitats (
    id     text primary key,                   -- 'iss', 'moon_base_rover', 'mars_base'
    label  text not null,
    data   jsonb not null
);

-- Reports: NASA PSI documents and, later, user uploads.
create table if not exists documents (
    id          serial primary key,
    origin      text not null check (origin in ('psi', 'upload')),
    psi_id      text references investigations(id),
    file        text not null,
    url         text,                          -- link to the original file
    sha1        text unique not null,          -- same file is never stored twice
    status      text not null default 'approved'
                check (status in ('processing', 'unreviewed', 'approved', 'rejected', 'failed')),
    n_pages     integer,
    created_at  timestamptz not null default now()
);

-- One row per PDF page: the full text, for display and citations ("file, PDF p. N").
create table if not exists pages (
    id           bigserial primary key,
    document_id  integer not null references documents(id) on delete cascade,
    page         integer not null,             -- PDF page, 1-based
    text         text not null,
    unique (document_id, page)
);
-- Search moved from pages to chunks (earlier versions of this schema had these on pages).
alter table pages drop column if exists embedding;
alter table pages drop column if exists tsv;

-- The search unit for RAG: ~250-word pieces of one page (never across pages, so every hit keeps its page).
--   tsv        full-text search: exact terms such as 'PMMA', 'BASS-II', '13.5'
--   embedding  vector search: same meaning in different words (BGE-M3, 1024 dimensions)
create table if not exists chunks (
    id           bigserial primary key,
    page_id      bigint not null references pages(id) on delete cascade,
    chunk_index  integer not null,             -- 0, 1, 2 ... within the page
    text         text not null,
    tsv          tsvector generated always as (to_tsvector('english', text)) stored,
    embedding    vector(1024),
    unique (page_id, chunk_index)
);
-- Moved from Gemini (768) to BGE-M3 (1024): vectors of different models can't be mixed, so an old-size
-- column is dropped (with its index) and re-added empty; push_data.py --embed then fills it again.
do $$ begin
    if (select format_type(atttypid, atttypmod) from pg_attribute
        where attrelid = 'chunks'::regclass and attname = 'embedding') <> 'vector(1024)' then
        alter table chunks drop column embedding;
        alter table chunks add column embedding vector(1024);
    end if;
end $$;
create index if not exists chunks_tsv on chunks using gin (tsv);
create index if not exists chunks_embedding on chunks using hnsw (embedding vector_cosine_ops);
