"""Flame Lab method vs trained models, on the same held-out test days.

The Flame Lab (app/services/droplet.py) answers with an inverse-distance vote / average of the 5 nearest tests of
the same fuel and diluent. The predictors (train_predictors.py) are linear models. This script scores both on the
SAME rows and the SAME grouped folds (whole test days held out), using the trainer's own load / split / metrics:

  python scripts/compare_nearest.py

Compared: P1 (droplet ending, 3 classes), P1b (went out early?), P7 (cool-flame ending), P6b (hot-flame end size /
start size). Writes models/NEAREST_VS_MODELS.md. Needs pandas + scikit-learn, like the trainer.
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_predictors as tp  # noqa: E402

# The Flame Lab's settings (app/services/droplet.py)
K_NEAREST = 5
SCALE_O2, SCALE_LOGP, SCALE_D0 = 3.0, math.log(1.25), 1.0
# columns a test needs to be used by the lab (it animates K and end sizes)
LAB_NEEDS = {"flex": ["burning_rate_raw", "droplet_d0_mm", "extinction_diameter_mm"],
             "cfi": ["khot_mm2_s", "droplet_d0_mm", "dext_hot_mm"]}
PIDS = ["P1", "P1b", "P7", "P6b"]


def prepare(pid):
    """Exactly the rows, target and folds train_predictors.run() uses."""
    cfg = tp.CONFIGS[pid]
    d = tp.load(cfg)
    need = list(dict.fromkeys(cfg["num"] + cfg["cat"] + cfg["inputs_num"] + cfg["inputs_cat"] + ["_y", cfg["group"]]))
    d = d.dropna(subset=need).reset_index(drop=True)
    return cfg, d


def dist(a, b):
    o2 = (a["o2_pct"] - b["o2_pct"]) / SCALE_O2
    lp = math.log(a["pressure_kpa"] / b["pressure_kpa"]) / SCALE_LOGP
    d0 = 0.0 if np.isnan(a["droplet_d0_mm"]) else (a["droplet_d0_mm"] - b["droplet_d0_mm"]) / SCALE_D0
    return math.sqrt(o2 * o2 + lp * lp + d0 * d0)


def nearest(test, pool):
    """The lab's 5 nearest tests (same fuel and diluent) with their weights."""
    same = pool[(pool.fuel == test["fuel"]) & (pool.diluent == test["diluent"])]
    scored = sorted(((dist(test, r), r) for _, r in same.iterrows()), key=lambda t: t[0])[:K_NEAREST]
    return [(1 / (dd + 0.05), r) for dd, r in scored]


def lab_oof(cfg, d, classes):
    """Out-of-fold answers of the lab method: vote shares (classes) or weighted mean (numbers)."""
    table = cfg["table"]
    usable = d.dropna(subset=LAB_NEEDS[table])
    splitter, _ = tp.split(d[cfg["group"]])
    P = np.zeros((len(d), len(classes))) if classes else np.zeros(len(d))
    fallback = 0
    for tr, te in splitter.split(d, d["_y"], d[cfg["group"]]):
        train = d.iloc[tr]
        pool = usable[usable.index.isin(train.index)]
        prior = train["_y"].value_counts(normalize=True) if classes else None
        for i in te:
            near = nearest(d.iloc[i], pool)
            if classes:
                votes = {}
                for w, r in near:
                    votes[r["_y"]] = votes.get(r["_y"], 0) + w
                if not votes:
                    fallback += 1
                    P[i] = [prior.get(c, 0.0) for c in classes]
                else:
                    s = sum(votes.values())
                    P[i] = [votes.get(c, 0) / s for c in classes]
            else:
                if not near:
                    fallback += 1
                    P[i] = train["_y"].mean()
                else:
                    P[i] = sum(w * r["_y"] for w, r in near) / sum(w for w, _ in near)
    return P, fallback


def compare(pid):
    cfg, d = prepare(pid)
    y = d["_y"]
    clf = cfg["task"] == "classification"
    classes = sorted(y.unique()) if clf else None
    L, B = tp.oof(cfg, d, cfg["num"], cfg["cat"], tp.linear, classes)
    N, fb = lab_oof(cfg, d, classes)
    m = tp.clf_metrics if clf else (lambda yy, p, _c=None: tp.reg_metrics(yy, p))
    rows = {"baseline (always guess)": m(y, B, classes), "trained model (linear)": m(y, L, classes),
            "Flame Lab (5 nearest)": m(y, N, classes)}
    if clf:
        rows["baseline (always guess)"]["roc_auc"] = None
    return {"pid": pid, "title": cfg["title"], "n": len(d), "cv": tp.split(d[cfg["group"]])[1],
            "rows": rows, "fallback": fb, "clf": clf,
            "confusion_lab": tp.confusion(y, N, classes) if clf else None}


def fmt(r):
    keys = ["accuracy", "balanced_accuracy", "macro_f1", "log_loss", "roc_auc"] if r["clf"] else ["mae", "rmse", "r2"]
    out = [f"## {r['pid']}: {r['title']}", "", f"Rows {r['n']} · CV: {r['cv']} · same folds for all three", "",
           "| | " + " | ".join(keys) + " |", "|---" * (len(keys) + 1) + "|"]
    for name, mt in r["rows"].items():
        out.append(f"| {name} | " + " | ".join("–" if mt.get(k) is None else f"{mt[k]:.3f}" for k in keys) + " |")
    if r["fallback"]:
        out.append(f"\nFlame Lab had no same-fuel/diluent neighbour for {r['fallback']} held-out rows (used the prior).")
    if r["clf"]:
        out += ["", "Note: the lab's vote shares can be exactly 0, which makes its log loss large when wrong.",
                "", "Confusion (Flame Lab, held-out):", "", "```", r["confusion_lab"].to_string(), "```"]
    return "\n".join(out) + "\n"


def main():
    parts = ["# Flame Lab (5 nearest tests) vs trained models", "",
             "Generated by `scripts/compare_nearest.py`. All three methods are scored on the same rows and the same "
             "held-out test days as `models/REPORT.md`.", ""]
    for pid in PIDS:
        txt = fmt(compare(pid))
        print(txt)
        parts.append(txt)
    (tp.OUT / "NEAREST_VS_MODELS.md").write_text("\n".join(parts), encoding="utf-8")
    print(f"written {tp.OUT / 'NEAREST_VS_MODELS.md'}")


if __name__ == "__main__":
    main()
