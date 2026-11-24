"""Small shared helpers: config, seeds, saving results. (Implemented - no TODOs.)"""
from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def load_config(path: str | Path = "configs/base.yaml", overrides: dict | None = None) -> dict:
    """Read the YAML config. `overrides` uses dotted keys, e.g. {"movement.threshold_frac": 0.2}."""
    with open(path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    for key, value in (overrides or {}).items():
        node = cfg
        parts = key.split(".")
        for p in parts[:-1]:
            node = node[p]
        node[parts[-1]] = value
    return cfg


def with_ablation(cfg: dict, name: str) -> dict:
    """Return a copy of cfg with one ablation from cfg['ablations'] applied."""
    out = copy.deepcopy(cfg)
    for key, value in cfg["ablations"][name].items():
        node = out
        parts = key.split(".")
        for p in parts[:-1]:
            node = node[p]
        node[parts[-1]] = value
    return out


def set_seed(seed: int) -> np.random.Generator:
    """Fix every random source we use and return a numpy Generator to pass around."""
    random.seed(seed)
    np.random.seed(seed)
    return np.random.default_rng(seed)


def results_dir(cfg: dict, tag: str | None = None) -> Path:
    """results/ (or results/ablations/<tag>/). Created if missing."""
    d = Path(cfg["paths"]["results"])
    if tag:
        d = d / "ablations" / tag
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"  saved {path}")


def save_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, default=float)
    print(f"  saved {path}")
