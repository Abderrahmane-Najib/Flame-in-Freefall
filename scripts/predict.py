"""Runtime for the trained predictors (P1-P8). Standard library only.

Loads models/<ID>.json (written by train_predictors.py) and answers one query:
model value, trust badge, 7 nearest real tests, caveats.

  python scripts/predict.py P3 '{"fuel":"propane","o2_pct":35,"pressure_kpa":101,"burner_fuel_pct":30,"fuel_flow_mg_s":1.2}'

The feature code here (derive / encode) is imported by the trainer, so training
and the app always compute inputs the same way.
"""
import json
import math
import sys
from pathlib import Path

MODELS = Path(__file__).resolve().parents[1] / "models"

GRAVITY_CAVEAT = "Microgravity evidence only. Moon/Mars gravity never tested."

# Trust badge thresholds, in standard deviations of the training inputs.
TESTED_HERE_DIST = 0.25   # a real test this close with the same categories
BETWEEN_MAX_DIST = 1.0    # beyond this, no test is near enough to interpolate
CATEGORY_PENALTY = 3.0    # distance added per categorical mismatch (prefer same fuel)
N_NEAREST = 7


def _num(v):
    """float or None (None, '', NaN all count as missing)."""
    if v is None or v == "":
        return None
    v = float(v)
    return None if math.isnan(v) else v


# CFI-G gas flames: stoichiometric mixture fraction (exact) and flame temperature (fit).
# Burner gas = fuel + N2 at burner_fuel_pct; chamber = O2 + N2 at o2_pct.
GAS = {  # molar mass g/mol, O2 per fuel (mol), lower heating value MJ/kg
    "ethane": (30.07, 3.5, 47.5), "propane": (44.10, 5.0, 46.35), "butane": (58.12, 6.5, 45.75)}
# Tad_est = 300 + A (1 - exp(-h / B)), h = Zst * Y_fuel * LHV (J/kg). Fitted to NASA's Tad column
# (177 CFI-G normal flames); train_predictors.py re-checks it (mean error ~21 K) on every run.
TAD_A, TAD_B = 2859.0, 2.4953e6


def gas_flame(fuel, burner_fuel_pct, o2_pct):
    """(zst_calc, tad_est_k) for a CFI-G normal flame, or (None, None)."""
    if fuel not in GAS or not burner_fuel_pct or o2_pct is None:
        return None, None
    w, nu, lhv = GAS[fuel]
    xf, xo = burner_fuel_pct / 100, o2_pct / 100
    yf = xf * w / (xf * w + (1 - xf) * 28.013)
    yo = xo * 32 / (xo * 32 + (1 - xo) * 28.013)
    z = 1 / (1 + (nu * 32 / w) * yf / yo)
    h = z * yf * lhv * 1e6
    return z, 300 + TAD_A * (1 - math.exp(-h / TAD_B))


FLEX_INTERACT = ["o2_pct", "pressure_kpa", "o2_partial_kpa", "co2_pct", "he_pct", "log_d0_mm"]


def derive(row):
    """Add derived inputs to a dict of raw inputs. Missing stays missing."""
    r = dict(row)
    r["zst_calc"], r["tad_est_k"] = gas_flame(r.get("fuel"), _num(r.get("burner_fuel_pct")), _num(r.get("o2_pct")))
    o2, p = _num(r.get("o2_pct")), _num(r.get("pressure_kpa"))
    r["o2_partial_kpa"] = o2 * p / 100 if o2 is not None and p is not None else None
    r["log_pressure_kpa"] = math.log(p) if p else None
    d0 = _num(r.get("droplet_d0_mm"))
    r["log_d0_mm"] = math.log(d0) if d0 else None
    r["o2_sq"] = o2 * o2 if o2 is not None else None
    # FLEX: heptane gets its own slope on each input (methanol = reference)
    if r.get("fuel") in ("heptane", "methanol"):
        hep = 1.0 if r["fuel"] == "heptane" else 0.0
        for c in FLEX_INTERACT:
            v = _num(r.get(c)) if c in r else None
            r["heptane_x_" + c] = hep * v if v is not None else None
    if "co2_pct" in r or "he_pct" in r:
        co2, he = _num(r.get("co2_pct")) or 0.0, _num(r.get("he_pct")) or 0.0
        r["diluent"] = "CO2" if co2 > 0 else "He" if he > 0 else "N2"
    return r


def encode(model, r):
    """Feature vector in the trainer's column order: scaled numerics, then one-hots."""
    x = []
    for f in model["features"]["numeric"]:
        x.append((_num(r[f["name"]]) - f["mean"]) / f["scale"])
    for f in model["features"]["categorical"]:
        x += [1.0 if r.get(f["name"]) == c else 0.0 for c in f["categories"]]
    return x


def raw_value(model, r):
    """Model output: class probabilities, or a number for regression."""
    x = encode(model, r)
    m = model["model"]
    if model["task"] == "classification":
        logits = [b + sum(w * xi for w, xi in zip(ws, x)) for ws, b in zip(m["coef"], m["intercept"])]
        classes = model["classes"]
        if len(logits) == 1:  # binary: one logit for classes[1]
            p1 = 1 / (1 + math.exp(-logits[0]))
            return {classes[0]: 1 - p1, classes[1]: p1}
        top = max(logits)
        e = [math.exp(z - top) for z in logits]
        s = sum(e)
        return {c: v / s for c, v in zip(classes, e)}
    y = m["intercept"][0] + sum(w * xi for w, xi in zip(m["coef"][0], x))
    return math.exp(y) if model.get("target_transform") == "log" else y


def _rule_hits(rules, r):
    ops = {"<": lambda a, b: a < b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b,
           ">=": lambda a, b: a >= b, "==": lambda a, b: a == b, "in": lambda a, b: a in b}
    hits = []
    for rule in rules:
        ok = True
        for c in rule["all"]:
            v = r.get(c["input"])
            if isinstance(v, (int, float)):
                v = _num(v)
            if v is None or not ops[c["op"]](v, c["value"]):
                ok = False
                break
        if ok:
            hits.append(rule)
    return hits


def nearest(model, r, k=N_NEAREST):
    num = model["inputs"]["numeric"]
    cat = model["inputs"]["categorical"]
    sd = model["input_scale"]
    scored = []
    for t in model["training_rows"]:
        d2 = sum(((_num(r[n]) - t[n]) / sd[n]) ** 2 for n in num)
        mism = sum(1 for c in cat if r.get(c) != t[c])
        scored.append((math.sqrt(d2), mism, t))
    scored.sort(key=lambda s: s[0] + CATEGORY_PENALTY * s[1])
    return [dict(t, distance=round(d, 3), same_category=(m == 0)) for d, m, t in scored[:k]]


def trust(model, r, near, rule_hits):
    if any(h["action"] == "never_tested" for h in rule_hits):
        return "outside"
    key = "|".join(str(r.get(c)) for c in model["inputs"]["categorical"])
    box = model["coverage"].get(key)
    if box is None:
        return "outside"
    for n in model["inputs"]["numeric"]:
        v = _num(r[n])
        if v < box[n][0] or v > box[n][1]:
            return "outside"
    same = [t for t in near if t["same_category"]]
    if not same or same[0]["distance"] > BETWEEN_MAX_DIST:
        return "outside"
    return "tested_here" if same[0]["distance"] <= TESTED_HERE_DIST else "between"


def load(pid):
    return json.loads((MODELS / f"{pid}.json").read_text(encoding="utf-8"))


def predict(pid, inputs, model=None):
    model = model or load(pid)
    needed = model["inputs"]["numeric"] + model["inputs"]["categorical"]
    missing = [n for n in needed if inputs.get(n) is None or inputs.get(n) == ""]
    if missing:
        raise ValueError(f"{pid}: missing inputs {missing}")
    r = derive(inputs)
    hits = _rule_hits(model.get("rules", []), r)
    near = nearest(model, r)
    badge = trust(model, r, near, hits)
    nearest_only = badge == "outside" or any(h["action"] in ("never_tested", "nearest_only") for h in hits)

    out = {
        "predictor": model["id"],
        "title": model["title"],
        "inputs": {n: inputs[n] for n in needed},
        "trust": badge,
        "notes": [h["message"] for h in hits],
        "baseline": model["baseline"],
        "nearest_tests": near,
        "caveats": [GRAVITY_CAVEAT] + model.get("caveats", []),
        "sources": model["sources"],
    }
    if not nearest_only:
        v = raw_value(model, r)
        if model["task"] == "classification":
            out["answer"] = {"most_likely": max(v, key=v.get),
                             "probabilities": {k: round(p, 3) for k, p in v.items()}}
        else:
            lo, hi = model["interval"]
            if model.get("target_transform") == "log":
                rng = [v * lo, v * hi]
            else:
                rng = [v + lo, v + hi]
            out["answer"] = {"value": round(v, 3), "unit": model["unit"],
                             "typical_range": [round(max(x, 0), 3) for x in rng]}
    return out


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    print(json.dumps(predict(sys.argv[1], json.loads(sys.argv[2])), indent=2))
