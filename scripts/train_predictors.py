"""Train predictors P1-P8 from data/psi/clean/*.csv.

  python scripts/train_predictors.py            # all
  python scripts/train_predictors.py P3 P4      # some

For each predictor:
  * main model: logistic regression (classes) or ridge linear regression (numbers)
  * challenger: shallow gradient boosting, same folds; reported, adopted only if it clearly wins
  * grouped CV: whole test days held out (leave-one-day-out if <= 15 days, else 10 group folds)
  * baseline: majority class / mean, computed on the training folds only
Writes models/<ID>.json (read by scripts/predict.py) and models/REPORT.md.
Needs pandas + scikit-learn (training only; the app runtime needs neither).
"""
import datetime
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, f1_score, log_loss,
                             mean_absolute_error, r2_score, roc_auc_score, average_precision_score)
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
import predict as runtime  # noqa: E402  (shared derive/encode)

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "psi" / "clean"
OUT = ROOT / "models"

# "Clearly wins" rule for the boosting challenger.
BOOST_MIN_GAIN = 0.10      # >= 10% lower log loss (classes) or MAE (numbers)
BOOST_MIN_BAL_ACC = 0.03   # and >= 3 points better balanced accuracy (classes)

LUNAR_NEAREST_ONLY = {
    "action": "nearest_only",
    "all": [{"input": "o2_pct", "op": ">=", "value": 30}, {"input": "pressure_kpa", "op": "<=", "value": 70.3}],
    "message": "Lunar-like air (O2 >= 30%, <= 70.3 kPa): only 20 real tests here, so no model value. See the nearest tests.",
}
FLEX_NEAR_LUNAR = {
    "action": "label",
    "all": [{"input": "o2_pct", "op": ">=", "value": 30}, {"input": "pressure_kpa", "op": ">", "value": 70.3},
            {"input": "pressure_kpa", "op": "<=", "value": 72.5}],  # same band as the API
    "message": "Near-lunar air (O2 >= 30%, 71-72 kPa): just above the lunar cutoff. Not lunar.",
}
CFI_O2_17_HE = {
    "action": "never_tested",
    "all": [{"input": "o2_pct", "op": "<", "value": 19}, {"input": "he_pct", "op": ">", "value": 0}],
    "message": "Never tested: helium was only used at 21% O2 in CFI.",
}
CFI_BLEND_5ATM = {
    "action": "nearest_only",
    "all": [{"input": "fuel", "op": "in", "value": ["[.60]/[.40] C12H26/iso-dodecane", "[.75]/[.25] C12H26/iso-dodecane"]},
            {"input": "pressure_kpa", "op": ">", "value": 400}],
    "message": "Blends at 5 atm: only 2 tests each, so no model value. See the nearest tests.",
}

SRC = {
    "cfig": ["data/psi/clean/cfig_normal.csv",
             "PSI-159 CFI-G Final Report (FinalRpt_ACME.CFI-G.pdf), Tables 1-2 p. 21-22"],
    "flex": ["data/psi/clean/flex.csv", "PSI-69 FLEX experimental table"],
    "cfi": ["data/psi/clean/cfi.csv", "PSI-39 CFI_DataSummary_Spreadsheet_Jan2021.xlsx",
            "PSI-39 CFI Science Final Report p. 6, p. 8-10"],
}

CFIG = dict(table="cfig_normal", group="day", sources=SRC["cfig"],
            keep=lambda d: d[d.burner_fuel_pct > 0],  # 2 aborted attempts with no fuel flow (Xf = 0, Tad #DIV/0!)
            inputs_num=["o2_pct", "pressure_kpa", "burner_fuel_pct", "fuel_flow_mg_s"], inputs_cat=["fuel"],
            num=["o2_pct", "pressure_kpa", "o2_partial_kpa", "burner_fuel_pct", "fuel_flow_mg_s"], cat=["fuel"],
            rules=[LUNAR_NEAREST_ONLY])
CFIG_BASE = CFIG["num"]
FLEX = dict(table="flex", group="test_date", sources=SRC["flex"],
            inputs_num=["o2_pct", "pressure_kpa", "co2_pct", "he_pct"], inputs_cat=["fuel"],
            num=["o2_pct", "pressure_kpa", "o2_partial_kpa", "co2_pct", "he_pct"], cat=["fuel", "diluent"],
            rules=[FLEX_NEAR_LUNAR])
CFI = dict(table="cfi", group="test_date", sources=SRC["cfi"],
           keep=lambda d: d[d.analysis_complete == True],  # noqa: E712
           inputs_num=["o2_pct", "pressure_kpa", "he_pct", "droplet_d0_mm"], inputs_cat=["fuel"],
           num=["o2_pct", "log_pressure_kpa", "he_pct", "droplet_d0_mm"], cat=["fuel"],
           rules=[CFI_O2_17_HE, CFI_BLEND_5ATM])

CONFIGS = {
    "P3": dict(CFIG, title="Will a gas flame ignite?", task="classification",
               num=CFIG_BASE + ["tad_est_k", "zst_calc"],
               variants={"plain inputs (no Tad, Zst)": CFIG_BASE,
                         "NASA's Tad, Zst columns": CFIG_BASE + ["tad_k_calculated", "zst"]},
               target=lambda d: d.ignition.map({"no": "no ignition", "yes": "ignited"}),
               caveats=["Normal (cabin-oxygen) flames only; inverse flames are different physics."]),
    "P4": dict(CFIG, title="Once lit, does a gas flame go out by itself?", task="classification",
               keep=lambda d: d[(d.ignition == "yes") & (d.burner_fuel_pct > 0)],
               variants={"+ estimated Tad, Zst": CFIG_BASE + ["tad_est_k", "zst_calc"]},
               target=lambda d: d.extinction_mode.map({"flow_terminated": "kept burning",
                                                       "self_extinguished": "went out by itself"}),
               caveats=["'Kept burning' means it burned until the fuel flow was cut."]),
    "P1": dict(FLEX, title="How does a droplet fire end?", task="classification",
               target=lambda d: d.test_end,
               variants={"+droplet size": FLEX["num"] + ["droplet_d0_mm"]},
               caveats=["'Disruption' (droplet broke apart) is not yet defined from a FLEX paper."]),
    "P1b": dict(FLEX, title="Does a droplet fire go out early?", task="classification",
                target=lambda d: d.test_end.map({"extinction": "went out early", "disruption": "burned on",
                                                 "completion": "burned on"}),
                caveats=["'Burned on' = disruption or completion (2-class version of P1)."]),
    "P2": dict(FLEX, title="Droplet burn time", task="regression", unit="s", transform="log",
               inputs_num=FLEX["inputs_num"] + ["droplet_d0_mm"],
               num=FLEX["num"] + ["log_d0_mm", "o2_sq"] + ["heptane_x_" + c for c in runtime.FLEX_INTERACT],
               variants={"no fuel-specific slopes, no O2^2": FLEX["num"] + ["log_d0_mm"]},
               target=lambda d: d.burn_time_s),
    "P5": dict(CFI, title="Hot-flame burn time", task="regression", unit="s", transform="log",
               num=CFI["num"] + ["pressure_kpa"],
               variants={"log pressure only": CFI["num"]},
               target=lambda d: d.hf_burn_time_s),
    "P6": dict(CFI, title="Hot-flame extinction diameter", task="regression", unit="mm",
               target=lambda d: d.dext_hot_mm),
    "P6b": dict(CFI, title="Hot-flame extinction diameter / initial droplet size", task="regression", unit="ratio",
                target=lambda d: d.dext_hot_mm / d.droplet_d0_mm),
    "P7": dict(CFI, title="Cool-flame end state", task="classification",
               target=lambda d: d.cool_flame_end.map({"early_extinction": "cool flame went out early",
                                                      "consumed_droplet": "cool flame consumed the droplet"}),
               caveats=["Reading of Dext,cool = 0 as 'consumed the droplet' is our interpretation (report p. 6), "
                        "not a NASA definition."]),
    "P8": dict(CFI, title="Will the flame reignite?", task="classification",
               inputs_num=["o2_pct", "pressure_kpa", "he_pct"], inputs_cat=[],
               num=["o2_pct", "log_pressure_kpa", "he_pct"], cat=[],
               target=lambda d: d.reignited.map({True: "reignited", False: "no reignition"}),
               caveats=["Small sample: 35 tests reignited."]),
}


# ----------------------------------------------------------------- data

def load(cfg):
    d = pd.read_csv(CLEAN / f"{cfg['table']}.csv")
    d = cfg.get("keep", lambda x: x)(d).copy()
    # derived inputs via the runtime's own code
    derived = pd.DataFrame([runtime.derive(r) for r in d.to_dict("records")], index=d.index)
    for c in ["o2_partial_kpa", "log_pressure_kpa", "log_d0_mm", "zst_calc", "tad_est_k", "o2_sq"] +             [c for c in derived if c.startswith("heptane_x_")]:
        d[c] = derived[c].astype(float)
    if cfg["table"] == "cfig_normal":  # our Zst / Tad must match NASA's calculated columns
        ok = d.zst.notna()
        zerr = (d.zst_calc - d.zst)[ok].abs().max()
        terr = (d.tad_est_k - d.tad_k_calculated)[ok].abs().mean()
        assert zerr < 1e-4 and terr < 30, f"Zst max err {zerr}, Tad mean err {terr:.1f} K"
    if "diluent" in derived and "diluent" in d:
        bad = (derived["diluent"] != d["diluent"]).sum()
        assert bad == 0, f"derived diluent differs from clean column on {bad} rows"
    d["_y"] = cfg["target"](d)
    return d


def split(groups):
    n = groups.nunique()
    return (LeaveOneGroupOut(), f"leave-one-group-out ({n} groups)") if n <= 15 else \
        (GroupKFold(n_splits=10), f"10-fold grouped ({n} groups)")


def pipe(num, cat, est):
    ct = ColumnTransformer([("num", StandardScaler(), num),
                            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat)])
    return Pipeline([("x", ct), ("m", est)])


def linear(task):
    return LogisticRegression(C=1.0, max_iter=5000) if task == "classification" else Ridge(alpha=1.0)


def boost(task):
    kw = dict(n_estimators=150, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=0)
    return GradientBoostingClassifier(**kw) if task == "classification" else GradientBoostingRegressor(**kw)


# ----------------------------------------------------------------- evaluation

def oof(cfg, d, num, cat, make, classes):
    """Out-of-fold predictions + training-fold baselines."""
    X, y, g = d[num + cat], d["_y"], d[cfg["group"]]
    splitter, _ = split(g)
    log = cfg.get("transform") == "log"
    if cfg["task"] == "classification":
        P, B = np.zeros((len(d), len(classes))), np.zeros((len(d), len(classes)))
    else:
        P, B = np.zeros(len(d)), np.zeros(len(d))
    for tr, te in splitter.split(X, y, g):
        m = pipe(num, cat, make(cfg["task"]))
        if cfg["task"] == "classification":
            m.fit(X.iloc[tr], y.iloc[tr])
            idx = [classes.index(c) for c in m.classes_]
            P[np.ix_(te, idx)] = m.predict_proba(X.iloc[te])
            prior = y.iloc[tr].value_counts(normalize=True)
            B[te] = [prior.get(c, 0.0) for c in classes]
        else:
            yt = np.log(y.iloc[tr]) if log else y.iloc[tr]
            m.fit(X.iloc[tr], yt)
            p = m.predict(X.iloc[te])
            P[te] = np.exp(p) if log else p
            B[te] = math.exp(yt.mean()) if log else yt.mean()
    return P, B


def clf_metrics(y, P, classes):
    yi = np.array([classes.index(v) for v in y])
    pred = P.argmax(1)
    onehot = np.eye(len(classes))[yi]
    Pc = np.clip(P, 1e-6, 1)
    out = {"accuracy": accuracy_score(yi, pred), "balanced_accuracy": balanced_accuracy_score(yi, pred),
           "macro_f1": f1_score(yi, pred, average="macro"),
           "log_loss": log_loss(yi, Pc / Pc.sum(1, keepdims=True), labels=range(len(classes))),
           "brier": float(((P - onehot) ** 2).sum(1).mean())}
    if len(classes) == 2:
        out["roc_auc"] = roc_auc_score(yi, P[:, 1]) if len(set(yi)) == 2 else None
        out["pr_auc_" + classes[1]] = average_precision_score(yi, P[:, 1])
    else:
        out["roc_auc"] = roc_auc_score(yi, P, multi_class="ovr", average="macro")
    return {k: (round(float(v), 4) if v is not None else None) for k, v in out.items()}


def reg_metrics(y, p):
    return {"mae": round(float(mean_absolute_error(y, p)), 4),
            "rmse": round(float(np.sqrt(((y - p) ** 2).mean())), 4),
            "r2": round(float(r2_score(y, p)), 4)}


def confusion(y, P, classes):
    pred = [classes[i] for i in P.argmax(1)]
    return pd.crosstab(pd.Series(list(y), name="actual"), pd.Series(pred, name="predicted")) \
        .reindex(index=classes, columns=classes, fill_value=0)


# ----------------------------------------------------------------- export

def export(cfg, pid, d, num, cat, classes, metrics, interval, cv_name):
    m = pipe(num, cat, linear(cfg["task"]))
    y = d["_y"]
    if cfg["task"] == "classification":
        m.fit(d[num + cat], y)
        assert list(m.classes_) == classes
    else:
        m.fit(d[num + cat], np.log(y) if cfg.get("transform") == "log" else y)
    sc = m.named_steps["x"].named_transformers_["num"]
    feats = {"numeric": [{"name": n, "mean": float(a), "scale": float(s)} for n, a, s in zip(num, sc.mean_, sc.scale_)],
             "categorical": []}
    if cat:
        oh = m.named_steps["x"].named_transformers_["cat"]
        feats["categorical"] = [{"name": n, "categories": [str(c) for c in cs]} for n, cs in zip(cat, oh.categories_)]
    est = m.named_steps["m"]
    coef = np.atleast_2d(est.coef_).tolist()
    intercept = np.atleast_1d(est.intercept_).tolist()

    inum, icat = cfg["inputs_num"], cfg["inputs_cat"]
    rows = []
    for r in d.to_dict("records"):
        row = {"test_id": str(r["test_id"]), "group": str(r[cfg["group"]]),
               "source_file": r["source_file"], "source_row": str(r["source_row"]),
               "lunar_air": bool(r.get("lunar_air", False)), "outcome": r["_y"]}
        row.update({n: float(r[n]) for n in inum})
        row.update({c: str(r[c]) for c in icat})
        if cfg["task"] == "regression":
            row["outcome"] = round(float(r["_y"]), 4)
        rows.append(row)
    coverage = {}
    keys = d[icat].astype(str).agg("|".join, axis=1) if icat else pd.Series("", index=d.index)
    for k, grp in d.groupby(keys):
        coverage[k] = {n: [float(grp[n].min()), float(grp[n].max())] for n in inum}

    if cfg["task"] == "classification":
        base = {"what": "always predict the most common outcome",
                "most_common": y.value_counts().idxmax(),
                "rate": round(float(y.value_counts(normalize=True).max()), 4)}
    else:
        base = {"what": "always predict the mean", "value": round(float(y.mean()), 4), "unit": cfg["unit"]}

    model = {
        "id": pid, "title": cfg["title"], "task": cfg["task"], "classes": classes if cfg["task"] == "classification" else None,
        "unit": cfg.get("unit"), "target_transform": cfg.get("transform"),
        "created": datetime.date.today().isoformat(),
        "data": {"table": cfg["table"], "n_rows": len(d), "group": cfg["group"],
                 "n_groups": int(d[cfg["group"]].nunique()), "cv": cv_name},
        "inputs": {"numeric": inum, "categorical": icat},
        "input_scale": {n: float(d[n].std()) or 1.0 for n in inum},
        "features": feats,
        "model": {"type": "logistic" if cfg["task"] == "classification" else "ridge",
                  "coef": coef, "intercept": intercept},
        "interval": interval,
        "baseline": base, "metrics": metrics, "coverage": coverage,
        "rules": cfg.get("rules", []), "caveats": cfg.get("caveats", []), "sources": cfg["sources"],
        "training_rows": rows,
    }
    # the runtime must reproduce sklearn exactly
    js = json.loads(json.dumps(model))
    for r, i in zip(d.to_dict("records")[:50], range(50)):
        v = runtime.raw_value(js, runtime.derive({k: r[k] for k in num + cat + inum + icat}))
        if cfg["task"] == "classification":
            sk = m.predict_proba(d[num + cat].iloc[[i]])[0]
            assert max(abs(v[c] - p) for c, p in zip(classes, sk)) < 1e-9
        else:
            sk = m.predict(d[num + cat].iloc[[i]])[0]
            sk = math.exp(sk) if cfg.get("transform") == "log" else sk
            assert abs(v - sk) < 1e-9 * max(1, abs(sk))
    OUT.mkdir(exist_ok=True)
    (OUT / f"{pid}.json").write_text(json.dumps(model, indent=1, default=str), encoding="utf-8")


# ----------------------------------------------------------------- main

def run(pid):
    cfg = CONFIGS[pid]
    d = load(cfg)
    need = list(dict.fromkeys(cfg["num"] + cfg["cat"] + cfg["inputs_num"] + cfg["inputs_cat"] + ["_y", cfg["group"]]))
    n0 = len(d)
    d = d.dropna(subset=need).reset_index(drop=True)
    dropped = n0 - len(d)
    num, cat = cfg["num"], cfg["cat"]
    classes = sorted(d["_y"].unique()) if cfg["task"] == "classification" else None
    _, cv_name = split(d[cfg["group"]])
    y = d["_y"]

    res = {"n_rows": len(d), "dropped_missing": dropped, "cv": cv_name}
    if cfg["task"] == "classification":
        res["class_counts"] = y.value_counts().to_dict()
        P, B = oof(cfg, d, num, cat, linear, classes)
        G, _ = oof(cfg, d, num, cat, boost, classes)
        res["linear"], res["baseline"], res["boosting"] = (clf_metrics(y, X, classes) for X in (P, B, G))
        res["baseline"]["roc_auc"] = None  # a constant guess has no ranking; fold artefacts make AUC meaningless
        res["confusion"] = confusion(y, P, classes)
        lin, gb = res["linear"], res["boosting"]
        res["boost_clearly_wins"] = (gb["log_loss"] <= (1 - BOOST_MIN_GAIN) * lin["log_loss"]
                                     and gb["balanced_accuracy"] >= lin["balanced_accuracy"] + BOOST_MIN_BAL_ACC)
        interval = None
    else:
        P, B = oof(cfg, d, num, cat, linear, classes)
        G, _ = oof(cfg, d, num, cat, boost, classes)
        res["linear"], res["baseline"], res["boosting"] = (reg_metrics(y, X) for X in (P, B, G))
        res["boost_clearly_wins"] = res["boosting"]["mae"] <= (1 - BOOST_MIN_GAIN) * res["linear"]["mae"]
        # 80% range from out-of-fold residuals (ratio for log targets)
        resid = (y / P) if cfg.get("transform") == "log" else (y - P)
        interval = [round(float(np.quantile(resid, 0.1)), 4), round(float(np.quantile(resid, 0.9)), 4)]
        res["interval_80"] = interval
    res["variants"] = {}
    for name, vnum in cfg.get("variants", {}).items():
        dv = d.dropna(subset=vnum).reset_index(drop=True)
        V, _ = oof(cfg, dv, vnum, cat, linear, classes)
        res["variants"][name] = dict(n_rows=len(dv), **(clf_metrics(dv["_y"], V, classes)
                                                        if cfg["task"] == "classification" else reg_metrics(dv["_y"], V)))
    metrics = {k: res[k] for k in ("linear", "baseline", "boosting", "variants", "boost_clearly_wins")}
    export(cfg, pid, d, num, cat, classes, metrics, interval, cv_name)
    return res


def fmt(pid, r):
    cfg = CONFIGS[pid]
    lines = [f"## {pid}: {cfg['title']}", "",
             f"Rows {r['n_rows']} (dropped {r['dropped_missing']} with missing inputs) · CV: {r['cv']}"]
    if "class_counts" in r:
        lines.append("Classes: " + ", ".join(f"{k} {v}" for k, v in r["class_counts"].items()))
        keys = ["accuracy", "balanced_accuracy", "macro_f1", "log_loss", "brier", "roc_auc"]
    else:
        keys = ["mae", "rmse", "r2"]
    lines += ["", "| | " + " | ".join(keys) + " |", "|---" * (len(keys) + 1) + "|"]
    for name in ["baseline", "linear", "boosting"]:
        lines.append(f"| {name} | " + " | ".join(str(r[name].get(k)) for k in keys) + " |")
    for name, v in r["variants"].items():
        lines.append(f"| linear {name} (n={v['n_rows']}) | " + " | ".join(str(v.get(k)) for k in keys) + " |")
    lines.append("")
    lines.append(f"Boosting clearly wins: **{r['boost_clearly_wins']}**")
    if "interval_80" in r:
        lines.append(f"80% range from held-out errors: {r['interval_80']} "
                     f"({'ratio to prediction' if CONFIGS[pid].get('transform') == 'log' else 'added to prediction'})")
    if "confusion" in r:
        lines += ["", "Confusion (linear, held-out):", "", "```", r["confusion"].to_string(), "```"]
    return "\n".join(lines) + "\n"


def main(ids):
    ids = ids or list(CONFIGS)
    report = ["# Predictor training report", "",
              f"Generated {datetime.date.today().isoformat()} by `scripts/train_predictors.py`. "
              "All scores are on held-out test days (grouped CV). Baselines use training folds only.", ""]
    for pid in ids:
        r = run(pid)
        txt = fmt(pid, r)
        print(txt)
        report.append(txt)
    if set(ids) == set(CONFIGS):
        (OUT / "REPORT.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
