from pydantic import BaseModel, Field


class SearchHit(BaseModel):
    score: float = Field(description="Reciprocal Rank Fusion score: higher = more relevant")
    by_meaning: bool = Field(description="Found by vector search")
    by_words: bool = Field(description="Found by full-text search")
    text: str = Field(description="The passage (~250 words of one page)")
    page: int = Field(description="PDF page, 1-based")
    file: str
    psi_id: str | None
    investigation: str | None = Field(description="Short name, e.g. BASS-II")
    origin: str = Field(description="psi = NASA PSI report, upload = added by a user")
    status: str = Field(description="approved, or unreviewed for uploads not yet checked")
    url: str | None = Field(description="Link to the original file at that page")
    cite: str = Field(description="Ready-to-display citation")


class SearchResponse(BaseModel):
    query: str
    mode: str = Field(description="hybrid, or text_only when the question could not be embedded")
    results: list[SearchHit]
