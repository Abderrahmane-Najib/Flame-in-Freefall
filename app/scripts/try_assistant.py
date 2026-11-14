"""Chat with the assistant in the terminal, to test its tools (shows each tool call).

Usage:  python app/scripts/try_assistant.py            (add --debug to see every message to/from the model)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.assistant import make_agent  # noqa: E402

agent = make_agent(debug="--debug" in sys.argv)
while True:
    q = input("\nYou: ").strip()
    if q in ("", "exit", "quit"):
        break
    agent.print_response(q, stream=True)  # Agno prints each tool call in the output
