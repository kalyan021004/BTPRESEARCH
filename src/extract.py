"""
Stage "train" of this project: compute every parameter for every subject.  (Run this first.)

    python -m src.extract                          # real data, path from configs/base.yaml
    python -m src.extract --data data/fake/EMG_Reaching_Healthy_Stroke --tag fake
    python -m src.extract --ablation threshold_low # one sensitivity check from the config

Writes (to results/ or results/ablations/<tag>/):
    subjects.csv               fixed subject list (order = leave-one-subject-out folds)
    parameters_long.csv        one row per subject x parameter x muscle/pair x target   [implemented]
    parameters_subject_muscle.csv  one row per subject x parameter x muscle/pair (secondary)
    parameters_subject.csv     one row per subject, one column per PRIMARY parameter
    parameters_split_half.csv  same, computed separately on targets half_a and half_b
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src import parameters as P
from src.dataset import common_targets, discover_subjects, load_trial, subject_table
from src.utils import load_config, results_dir, save_csv, set_seed, with_ablation


def compute_long(subjects, targets, cfg, halves: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run every parameter function. Functions still raising NotImplementedError are skipped with a note.

    Returns (long, half_rows). half_rows holds the PER_SUBJECT parameters (P7, P9, P10) recomputed on
    the trials of each split half ({"a": [1, 3, 5], ...}), with a column `half`; per-trial parameters
    need no recomputation (their halves are taken from `long`)."""
    rows, half_rows, skipped = [], [], set()
    for i, s in enumerate(subjects, 1):
        print(f"  [{i}/{len(subjects)}] {s.sid}", flush=True)
        trials = [load_trial(s, t, cfg) for t in targets]
        for tr in trials:
            if len(tr.movements) != cfg["data"]["expected_movements_per_target"]:
                print(f"      [check] Target {tr.target}: {len(tr.movements)} movements")
        jobs = [(f, tr) for tr in trials for f in P.PER_TRIAL] + [(f, trials) for f in P.PER_SUBJECT]
        for fn, arg in jobs:
            try:
                out = fn(arg, cfg)
            except NotImplementedError:
                skipped.add(fn.__name__)
                continue
            rows += [{"subject": s.sid, "group": s.group, **r} for r in out]
        for h, h_targets in (halves or {}).items():
            sub = [tr for tr in trials if tr.target in h_targets]
            for fn in P.PER_SUBJECT:
                if fn.__name__ in skipped:
                    continue
                half_rows += [{"subject": s.sid, "group": s.group, "half": h, **r} for r in fn(sub, cfg)]
    if skipped:
        print(f"  not implemented yet (skipped): {sorted(skipped)}")
    return pd.DataFrame(rows), pd.DataFrame(half_rows)


def to_subject_level(long: pd.DataFrame, targets: list[int]) -> pd.DataFrame:
    """One row per subject, one column per PRIMARY parameter (P1 ... P10).

    Aggregation rule (fixed in advance - do not change after seeing results):
      1. keep rows whose target is in `targets` or "ALL";
      2. per subject x parameter x muscle: mean over targets;
      3. per subject x parameter: mean over muscles / pairs  -> the primary value;
      4. columns: subject, group, P1_fragmentation, ..., P10_synergy_vaf1 (only those present).
    Also save per-muscle values (step 2 output) as parameters_subject_muscle.csv for the secondary analysis.
    """
    pm = per_muscle_level(long, targets)
    wide = (pm.groupby(["subject", "group", "parameter"], sort=False)["value"].mean()
              .unstack("parameter").reset_index())
    params = sorted([c for c in wide.columns if c not in ("subject", "group")], key=_param_number)
    order = list(dict.fromkeys(long["subject"]))                    # keep the fixed subjects.csv order
    wide = wide.set_index("subject").loc[order].reset_index()
    return wide[["subject", "group", *params]]


def per_muscle_level(long: pd.DataFrame, targets: list[int]) -> pd.DataFrame:
    """Steps 1-2 of to_subject_level: one row per subject x parameter x muscle/pair; value = mean over
    targets (NaN targets skipped), n_targets = targets with a finite value, n = summed movements/windows."""
    keep = long["target"].astype(str).isin([str(t) for t in targets] + ["ALL"])
    d = long[keep].assign(finite=lambda x: np.isfinite(x["value"]))
    return (d.groupby(["subject", "group", "parameter", "muscle"], sort=False)
              .agg(value=("value", "mean"), n_targets=("finite", "sum"), n=("n", "sum")).reset_index())


def split_half_table(long: pd.DataFrame, half_rows: pd.DataFrame, halves: dict) -> pd.DataFrame:
    """parameters_split_half.csv: columns subject, group, half, P1 ... P10, same aggregation as the main
    table. Per-trial parameters use the half's targets from `long`; P7, P9, P10 use `half_rows`."""
    per_trial = long[long["target"].astype(str) != "ALL"]
    out = []
    for h, h_targets in halves.items():
        hr = half_rows[half_rows["half"] == h].drop(columns="half") if len(half_rows) else half_rows
        out.append(to_subject_level(pd.concat([per_trial, hr], ignore_index=True), h_targets).assign(half=h))
    df = pd.concat(out, ignore_index=True)
    return df[["subject", "group", "half", *[c for c in df.columns if c.startswith("P")]]]


def _param_number(name: str) -> int:
    """'P10_synergy_vaf1' -> 10 (for column order)."""
    return int(name.split("_")[0][1:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/base.yaml")
    ap.add_argument("--data", help="override paths.data_root")
    ap.add_argument("--tag", help="write to results/ablations/<tag>/ (e.g. fake)")
    ap.add_argument("--ablation", help="name of an entry in config 'ablations'")
    a = ap.parse_args()

    cfg = load_config(a.config, {"paths.data_root": a.data} if a.data else None)
    if a.ablation:
        cfg = with_ablation(cfg, a.ablation)
    set_seed(cfg["seed"])
    out = results_dir(cfg, "_".join(x for x in (a.tag, a.ablation) if x) or None)   # e.g. fake_threshold_low

    subjects = discover_subjects(Path(cfg["paths"]["data_root"]))
    targets = common_targets(subjects) if cfg["data"]["targets"] == "common" else cfg["data"]["targets"]
    print(f"{sum(s.group == 'healthy' for s in subjects)} healthy, {sum(s.group == 'stroke' for s in subjects)} "
          f"stroke; targets used: {targets}")
    save_csv(subject_table(subjects), out / "subjects.csv")

    rh = cfg["split"]["reliability_halves"]
    halves = {"a": [t for t in rh["half_a"] if t in targets], "b": [t for t in rh["half_b"] if t in targets]}
    long, half_rows = compute_long(subjects, targets, cfg, halves)
    save_csv(long, out / "parameters_long.csv")
    save_csv(per_muscle_level(long, targets), out / "parameters_subject_muscle.csv")
    save_csv(to_subject_level(long, targets), out / "parameters_subject.csv")
    save_csv(split_half_table(long, half_rows, halves), out / "parameters_split_half.csv")


if __name__ == "__main__":
    main()
