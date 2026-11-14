"""Hybrid search over report chunks: full-text (exact terms) + vector (meaning), merged with
Reciprocal Rank Fusion (RRF): each chunk scores 1/(60 + rank) in each list it appears in.

If the question cannot be embedded (model not available), it falls back to full-text only and says so.
"""

from database.connection import connect
from services.embeddings import embed, to_pgvector

RRF_K = 60        # standard RRF constant: dampens the weight of the very first ranks
CANDIDATES = 50   # chunks taken from each list before merging

SQL = """
with
q_vec as (select %(vec)s::vector as v),
-- the question's words joined with OR ('|'), so a long question still matches chunks with some of its words
q_txt as (select nullif(replace(plainto_tsquery('english', %(q)s)::text, '&', '|'), '')::tsquery as t),
allowed as (
    select c.id
    from chunks c join pages p on p.id = c.page_id join documents d on d.id = p.document_id
    where d.status = any(%(statuses)s) and (%(psi_id)s::text is null or d.psi_id = %(psi_id)s)
      and (%(doc_id)s::int is null or d.id = %(doc_id)s)
),
by_vector as (
    select c.id, row_number() over (order by c.embedding <=> (select v from q_vec)) as rank
    from chunks c join allowed a on a.id = c.id
    where c.embedding is not null and (select v from q_vec) is not null
    order by c.embedding <=> (select v from q_vec)
    limit %(n)s
),
by_text as (
    select c.id, row_number() over (order by ts_rank_cd(c.tsv, q_txt.t) desc) as rank
    from chunks c join allowed a on a.id = c.id, q_txt
    where q_txt.t is not null and c.tsv @@ q_txt.t
    order by ts_rank_cd(c.tsv, q_txt.t) desc
    limit %(n)s
),
fused as (
    select id, sum(1.0 / (%(rrf_k)s + rank)) as score,
           bool_or(src = 'vector') as by_meaning, bool_or(src = 'text') as by_words
    from (select id, rank, 'vector' as src from by_vector
          union all
          select id, rank, 'text' as src from by_text) both_lists
    group by id
)
select round(f.score::numeric, 4)::float as score, f.by_meaning, f.by_words,
       c.text, p.page, d.file, d.psi_id, i.name as investigation, d.origin, d.status,
       case when d.url is not null then d.url || '#page=' || p.page
            when d.origin = 'upload' then '/uploads/' || d.id || '/pages/' || p.page end as url  -- API path
from fused f
join chunks c on c.id = f.id
join pages p on p.id = c.page_id
join documents d on d.id = p.document_id
left join investigations i on i.id = d.psi_id
order by f.score desc
limit %(k)s
"""


def search(q: str, psi_id: str | None = None, k: int = 8, include_unreviewed: bool = False,
           document_id: int | None = None) -> dict:
    """document_id: only this document (an upload's own chat); include_unreviewed: also uploads not yet approved."""
    try:
        vec = to_pgvector(embed([q])[0])
        mode = "hybrid"
    except Exception as e:  # the search still works on words alone
        vec, mode = None, f"text_only ({type(e).__name__})"
    statuses = ["approved", "unreviewed"] if include_unreviewed else ["approved"]
    with connect() as conn:
        hits = conn.execute(SQL, {"vec": vec, "q": q, "psi_id": psi_id, "statuses": statuses,
                                  "doc_id": document_id, "n": CANDIDATES, "rrf_k": RRF_K, "k": k}).fetchall()
    for h in hits:
        h["cite"] = f"{h['investigation'] or h['psi_id'] or 'Upload'}: {h['file']}, PDF p. {h['page']}"
    return {"query": q, "mode": mode, "results": hits}
