"""Runs the assistant for one question and turns Agno's stream into simple events for the UI.

Events, one JSON object per line (NDJSON):
  {"type": "session", "session_id": "..."}             first: send it back with the next question
  {"type": "tool", "name": "...", "args": {...}}       the assistant looks something up
  {"type": "text", "content": "..."}                   a piece of the answer, in order
  {"type": "error", "message": "..."}                  the run failed (e.g. model rate limit)
  {"type": "done"}                                     last
"""

import json
import uuid
from collections.abc import Iterator

from services.assistant import clean_citation, make_agent


def _line(event: dict) -> str:
    return json.dumps(event, default=str) + "\n"


def chat_events(message: str, session_id: str | None, persona: str) -> Iterator[str]:
    session_id = session_id or str(uuid.uuid4())
    yield _line({"type": "session", "session_id": session_id})
    try:
        # stream_events=True: also tool-call events, not only the answer text
        for chunk in make_agent(persona).run(message, session_id=session_id, stream=True, stream_events=True):
            # Agno event names (docs.agno.com/agents/running-agents); compared as strings
            if chunk.event == "RunContent" and chunk.content and (text := clean_citation(chunk.content)):
                yield _line({"type": "text", "content": text})
            elif chunk.event == "ToolCallStarted":
                yield _line({"type": "tool", "name": chunk.tool.tool_name, "args": chunk.tool.tool_args})
            elif chunk.event == "RunError":
                yield _line({"type": "error", "message": str(chunk.content)})
    except Exception as e:  # the stream has started: report the error as an event, not an HTTP status
        yield _line({"type": "error", "message": f"{type(e).__name__}: {e}"})
    yield _line({"type": "done"})
