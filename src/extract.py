"""
Stage "train" of this project: compute every parameter for every subject.  (Run this first.)

    python -m src.extract                          # real data, path from configs/base.yaml
    python -m src.extract --data data/fake/EMG_Reaching_Healthy_Stroke --tag fake
    python -m src.extract --ablation threshold_low # one sensitivity check from the config

Writes (to results/ or results/ablations/<tag>/):
    subjects.csv               fixed subject list (order = leave-one-subject-out folds)
    parameters_long.csv        one row per subject x parameter x muscle/pair x target   [implemented]
    parameters_subject.csv     one row per subject, one column per PRIMARY parameter     [TODO]
    parameters_split_half.csv  same, computed separately on targets half_a and half_b     [TODO]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src import parameters as P
from src.dataset import common_targets, discover_subjects, load_trial, subject_table
from src.utils import load_config, results_dir, save_csv, set_seed, with_ablation


def compute_long(subjects, targets, cfg) -> pd.DataFrame:
    """Run every parameter function. Functions still raising NotImplementedError are skipped with a note."""
    rows, skipped = [], set()
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
    if skipped:
        print(f"  not implemented yet (skipped): {sorted(skipped)}")
    return pd.DataFrame(rows)


def to_subject_level(long: pd.DataFrame, targets: list[int]) -> pd.DataFrame:
    """One row per subject, one column per PRIMARY parameter (P1 ... P10).

    TODO: implement. Aggregation rule (fixed in advance - do not change after seeing results):
      1. keep rows whose target is in `targets` or "ALL";
      2. per subject x parameter x muscle: mean over targets;
      3. per subject x parameter: mean over muscles / pairs  -> the primary value;
      4. columns: subject, group, P1_fragmentation, ..., P10_synergy_vaf1 (only those present).
    Also save per-muscle values (step 2 output) as parameters_subject_muscle.csv for the secondary analysis.
    """
    raise NotImplementedError


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

    long = compute_long(subjects, targets, cfg)
    save_csv(long, out / "parameters_long.csv")

    # TODO: subject-level table (all targets) and split-half tables, e.g.
    #   save_csv(to_subject_level(long, targets), out / "parameters_subject.csv")
    #   ha, hb = cfg["split"]["reliability_halves"]["half_a"], [...]["half_b"]
    #   build parameters_split_half.csv with columns subject, group, half ("a"/"b"), P1 ... P10.
    #   NOTE: P7, P9, P10 use all trials at once -> for the halves, call those functions again
    #   with only the trials of that half (do not reuse the "ALL" rows).


if __name__ == "__main__":
    main()
