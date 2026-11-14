"""The card agent: drafts an investigation card for an uploaded report, in the same shape as the NASA cards.

It never sees the whole report (Groq free tier: 8,000 tokens a minute). It gets the passages that the
search finds for a few fixed questions, and every point it writes must give the page it comes from.
Points whose page is not among the passages it was shown are dropped; the cite and url are built here,
never written by the model. The draft waits for the user's approval (services/uploads.py).
"""

from typing import Literal

from agno.agent import Agent
from agno.models.groq import Groq
from pydantic import BaseModel, Field

from core.config import GROQ_API_KEY, GROQ_MODEL
from services.search import search

# What a card needs; each question pulls the passages most likely to answer it.
QUESTIONS = [
    "objective and purpose of the experiment",
    "fuel or material burned, sample size and geometry",
    "oxygen concentration, pressure, flow speed and gravity conditions",
    "main results, findings and conclusions",
    "limitations, uncertainties and future work",
]
HITS_PER_QUESTION = 4
MAX_WORDS = 3000  # passages sent to the model, ~4,000 tokens


class Point(BaseModel):
    text: str = Field(description="One or two plain sentences, only what the passages say")
    page: int = Field(description="The PDF page of the passage it comes from")


class CardDraft(BaseModel):
    name: str = Field(description="Short name, e.g. the experiment acronym (max 40 characters)")
    title: str = Field(description="Full title of the study")
    fuel_type: Literal["solid", "droplet", "gas", "smoke", "ground"] = Field(
        description="solid material / liquid droplet / gas flame / smoke & detection / ground lab study")
    safety_jobs: list[Literal["prevention", "detection", "suppression"]] = Field(
        description="Fire-safety jobs the results inform")
    in_space: bool | None = Field(description="True if tests ran in space, false if on the ground, null if unclear")
    materials: list[str] = Field(description="Fuels or materials burned, by name (e.g. 'PMMA', 'n-heptane')")
    summary: Point
    findings: list[Point] = Field(description="Up to 6 measured results, each with numbers and conditions if given")
    limitations: list[Point] = Field(description="Up to 3 limitations the report states")


INSTRUCTIONS = [
    "You write a short card for a combustion / fire-safety report, using ONLY the passages given.",
    "Each passage starts with its PDF page. Every point must give the page of the passage it comes from.",
    "Copy numbers and conditions exactly; never add knowledge that is not in the passages.",
    "Keep measured results apart from suggestions. A finding holds only for the conditions it states.",
    "If the passages do not say something, leave the list empty or use null.",
]


def _passages(doc_id: int) -> list[dict]:
    seen, out, words = set(), [], 0
    for q in QUESTIONS:
        for h in search(q, k=HITS_PER_QUESTION, include_unreviewed=True, document_id=doc_id)["results"]:
            n = len(h["text"].split())
            if h["text"] in seen or words + n > MAX_WORDS:
                continue
            seen.add(h["text"])
            out.append(h)
            words += n
    return sorted(out, key=lambda h: h["page"])


def _point(p: Point, by_page: dict) -> dict | None:
    hit = by_page.get(p.page)
    if not hit:  # a page the model was not shown: not traceable, dropped
        return None
    return {"text": p.text, "src": "upload", "where": str(p.page), "cite": hit["cite"], "url": hit["url"]}


def draft_card(doc_id: int, file: str) -> dict:
    """Returns the draft card, or raises ValueError if the model gives no usable answer."""
    passages = _passages(doc_id)
    if not passages:
        raise ValueError("no passages found in the report")
    by_page = {h["page"]: h for h in passages}
    prompt = f"Report: {file}\n\n" + "\n\n".join(f"[PDF p. {h['page']}]\n{h['text']}" for h in passages)

    agent = Agent(model=Groq(id=GROQ_MODEL, api_key=GROQ_API_KEY), instructions=INSTRUCTIONS,
                  output_schema=CardDraft, use_json_mode=True)
    d = agent.run(prompt).content
    if not isinstance(d, CardDraft):
        raise ValueError(f"the card agent did not return a valid card: {str(d)[:200]}")

    summary = _point(d.summary, by_page)
    findings = [x for p in d.findings[:6] if (x := _point(p, by_page))]
    limitations = [x for p in d.limitations[:3] if (x := _point(p, by_page))]
    return {
        "name": d.name[:40],
        "title": d.title,
        "origin": "upload",
        "in_space": d.in_space,
        "fuel_type": d.fuel_type,
        "hardware_group": None,
        "fire_safety": {"jobs": sorted(set(d.safety_jobs)), "psi_label": None},
        "summary": {"text": summary["text"], "sources": [summary]} if summary else None,
        "findings": findings,
        "limitations": limitations,
        "conditions": {"fuels": [{"name": m, "tests": 0} for m in d.materials]},  # named, not counted
        "tests": {"available": False, "count": 0},
        "documents": {"file": file},
        "review": {
            "status": "draft",
            "note": "Drafted by the FlameScope card agent from the uploaded report; check every point against "
                    "its page before approving. Not NASA PSI data.",
            "points_dropped": (len(d.findings[:6]) - len(findings)) + (len(d.limitations[:3]) - len(limitations))
                              + (summary is None),
        },
    }
