"""Trained predictors P1-P8: models/<ID>.json, written by scripts/train_predictors.py (linear models, held-out
scores in models/REPORT.md). The runtime is scripts/predict.py, which the trainer also imports, so the app and the
training compute inputs the same way; this module only loads it (by file path, so scripts/ never shadows app
modules) and adds a short summary per model.

Deploy: the image must contain models/ and scripts/predict.py next to app/ (build from the repo root).
"""

import importlib.util
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("psi_predict", ROOT / "scripts" / "predict.py")
runtime = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runtime)

IDS = tuple(sorted(p.stem for p in (ROOT / "models").glob("P*.json")))


@lru_cache(maxsize=None)
def model(pid: str) -> dict:
    return runtime.load(pid)


def run(pid: str, inputs: dict) -> dict:
    """Model answer (or nearest tests only), trust badge, notes, caveats. ValueError on missing inputs."""
    return runtime.predict(pid, inputs, model(pid))


def summary(pid: str) -> dict:
    """What a UI needs to present the model honestly: inputs, tested ranges and the held-out scores."""
    m = model(pid)
    return {
        "id": m["id"], "title": m["title"], "task": m["task"], "classes": m["classes"], "unit": m["unit"],
        "inputs": m["inputs"], "coverage": m["coverage"], "data": m["data"],
        "held_out": {"model": m["metrics"]["linear"], "always_guess_baseline": m["metrics"]["baseline"]},
        "caveats": m["caveats"], "sources": m["sources"],
    }
