"""BGE-M3 embeddings (local model, no API quota), shared by the data push (chunks) and the API (questions).

Both must use the same model and size, or vectors cannot be compared. Runs on the GPU if there is one,
else the CPU; the vectors are the same either way. The model (~2.3 GB) is downloaded on first use.
"""

MODEL = "BAAI/bge-m3"
DIM = 1024        # must match vector(1024) in database/schema.sql
MAX_TOKENS = 512  # our chunks are ~250 words (~350 tokens); a shorter limit keeps it fast

_model = None


def _get_model():
    global _model
    if _model is None:
        import torch
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL, device="cuda" if torch.cuda.is_available() else "cpu")
        _model.max_seq_length = MAX_TOKENS
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    """One normalized vector per text (BGE-M3 needs no query/document prefix)."""
    return _get_model().encode(texts, normalize_embeddings=True).tolist()


def to_pgvector(values: list[float]) -> str:
    """Text form that PostgreSQL casts with ::vector."""
    return "[" + ",".join(f"{x:.6f}" for x in values) + "]"
