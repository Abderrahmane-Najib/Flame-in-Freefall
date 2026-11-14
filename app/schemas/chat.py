from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000, description="The user's question")
    session_id: str | None = Field(None, description="Send back the id from the first answer to keep the conversation")
    persona: Literal["student", "researcher", "engineer"] = Field("researcher", description="Language and depth")
