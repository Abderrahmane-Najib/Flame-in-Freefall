from typing import Literal

from pydantic import BaseModel, Field


class UploadChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000, description="The user's question about the uploaded report")
    session_id: str | None = Field(None, description="Send back the id from the first answer to keep the conversation")
    persona: Literal["student", "researcher", "engineer"] = Field("researcher", description="Language and depth")


class ApproveRequest(BaseModel):
    card: dict | None = Field(None, description="The card as the user edited it; empty = the drafted card as is")
