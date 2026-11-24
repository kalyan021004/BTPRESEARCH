"""
Stage "evaluate": statistics on the subject-level parameters.   (Run after src.extract.)

    python -m src.evaluate                 # reads results/parameters_subject.csv etc.
    python -m src.evaluate --tag fake

The SUBJECT is the unit of analysis (12 healthy vs 10 stroke). Never treat movements, windows or
targets as independent samples.

Writes (results/ or results/ablations/<tag>/):
    group_comparison.csv             primary table: one row per parameter                 [TODO]
    group_comparison_per_muscle.csv  secondary: one row per parameter x muscle/pair       [TODO]
    reliability.csv                  split-half ICC per parameter and group               [TODO]
    correlation.csv                  Spearman matrix between primary parameters           [TODO]
    composite.json, composite_scores.csv, composite_selection.csv                         [TODO]
    summary.json                     the key numbers the report quotes                    [TODO]
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from src.utils import load_config, results_dir, save_csv, save_json, set_seed


# ---------------------------------------------------------------------------- statistics helpers
def cliffs_delta(h: np.ndarray, s: np.ndarray) -> float:
    """TODO: delta = P(stroke > healthy) - P(stroke < healthy), over all pairs. Range -1..1."""
    raise NotImplementedError


def auc_stroke_higher(h: np.ndarray, s: np.ndarray) -> float:
    """TODO: AUC = P(stroke > healthy) + 0.5 * P(tie)  ( = (delta + 1) / 2 ).
    0.5 = no separation. Values < 0.5 mean stroke is LOWER; also report max(AUC, 1 - AUC) as
    'separation' so parameters that go down in stroke are ranked fairly."""
    raise NotImplementedError


def hedges_g(h: np.ndarray, s: np.ndarray) -> float:
    """TODO: (mean_s - mean_h) / pooled SD * (1 - 3 / (4 (n_h + n_s) - 9))."""
    raise NotImplementedError


def bootstrap_ci(h, s, stat, rng, n_boot) -> tuple[float, float]:
    """TODO: resample subjects WITH replacement WITHIN each group; 2.5 / 97.5 percentiles of stat."""
    raise NotImplementedError


def bh_fdr(p: np.ndarray) -> np.ndarray:
    """TODO: Benjamini-Hochberg q-values (keep NaN where p is NaN)."""
    raise NotImplementedError


def icc_3_1(Y: np.ndarray) -> float:
    """TODO: ICC(3,1) two-way mixed, consistency, single measure. Y: subjects x 2 halves.
    ICC = (MS_rows - MS_error) / (MS_rows + (k - 1) MS_error)."""
    raise NotImplementedError


# ---------------------------------------------------------------------------- analyses
def group_comparison(df: pd.DataFrame, cfg: dict, rng) -> pd.DataFrame:
    """TODO. For each primary parameter column:
    n_h, n_s, median + IQR per group, Mann-Whitney U two-sided p, Cliff's delta [95 % CI],
    Hedges g, AUC [95 % CI], separation = max(AUC, 1-AUC), BH q across the PRIMARY parameters,
    expected direction (from config), observed direction, 'as_expected' (bool; two-sided ones -> NA).
    Sort by separation, descending."""
    raise NotImplementedError


def reliability(split: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """TODO. From parameters_split_half.csv: for each parameter and group, ICC(3,1) between half a and
    half b across subjects, SEM = SD * sqrt(1 - ICC), MDC95 = 1.96 * sqrt(2) * SEM, rating
    (<0.5 poor, 0.5-0.75 moderate, 0.75-0.9 good, >0.9 excellent)."""
    raise NotImplementedError


def composite_loso(df: pd.DataFrame, cfg: dict, rng) -> dict:
    """TODO. Leave-one-subject-out composite score, in the fixed order of subjects.csv:
    for each left-out subject:
      1. on the TRAINING subjects only, rank parameters by Mann-Whitney p (ties: |delta|), take top k
         (cfg stats.composite_top_k);
      2. z-score the left-out subject vs the training HEALTHY mean / SD of each chosen parameter,
         multiply by the sign of the training difference (so + always means 'more stroke-like');
      3. composite = mean of those signed z.
    Report: AUC of composite with bootstrap CI, permutation p (shuffle labels, repeat the WHOLE
    procedure n_perm times), and how often each parameter was selected (selection stability).
    Selection MUST happen inside the fold - selecting on all data first would inflate the AUC."""
    raise NotImplementedError


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/base.yaml")
    ap.add_argument("--tag")
    a = ap.parse_args()
    cfg = load_config(a.config)
    rng = set_seed(cfg["seed"])
    res = results_dir(cfg, a.tag)

    # TODO: wire the analyses together:
    # df = pd.read_csv(res / "parameters_subject.csv")
    # save_csv(group_comparison(df, cfg, rng), res / "group_comparison.csv")
    # secondary per-muscle table from parameters_subject_muscle.csv (BH across ALL its rows)
    # save_csv(reliability(pd.read_csv(res / "parameters_split_half.csv"), cfg), res / "reliability.csv")
    # Spearman correlation between primary parameters (all subjects) -> correlation.csv
    # save_json(composite_loso(df, cfg, rng), res / "composite.json") (+ scores / selection CSVs)
    # summary.json: n per group, number of parameters with q < alpha, best parameter + its AUC,
    #               composite AUC [CI] and permutation p - everything the report text quotes.
    raise NotImplementedError("evaluate.main: see TODOs")


if __name__ == "__main__":
    main()
