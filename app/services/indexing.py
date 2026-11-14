"""Turning report text into search pieces, shared by push_data.py (NASA reports) and uploads.

A page is cleaned, then cut into ~CHUNK_WORDS-word chunks that never cross a page, so every hit keeps its page.
"""

import re

CHUNK_WORDS = 250     # words per chunk
CHUNK_OVERLAP = 50    # words repeated from the previous chunk, so a sentence cut at a border is whole once
EMBED_BATCH = 50      # chunks per model call (model and size: services/embeddings.py)
MIN_PAGE_CHARS = 40   # shorter pages are blank or image-only: skipped


def clean_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text.replace("\x00", ""))
    return re.sub(r"\n\s*\n+", "\n", text).strip()


def split_words(text: str) -> list[str]:
    """~CHUNK_WORDS-word pieces with CHUNK_OVERLAP words of overlap. A short page is one chunk."""
    words = text.split()
    if len(words) <= CHUNK_WORDS:
        return [" ".join(words)]
    step = CHUNK_WORDS - CHUNK_OVERLAP
    out = []
    for start in range(0, len(words), step):
        out.append(" ".join(words[start:start + CHUNK_WORDS]))
        if start + CHUNK_WORDS >= len(words):
            break
    return out


def embed_text(file: str, page: int, text: str) -> str:
    """What is embedded: the document name and page in front of the text help the model place the chunk."""
    return f"{file}, page {page}\n{text}"
