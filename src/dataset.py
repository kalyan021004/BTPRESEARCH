"""
Data loading for the Mendeley dataset (Israely, Leisman & Carmeli 2019, DOI 10.17632/f4hh43nd78.2).

IMPLEMENTED AND TESTED on real files - do not rewrite; extend only if needed.

Facts about the real files (found by opening them):
- Delsys EMGworks text export, TAB-separated even though named .csv, values in volts,
  only 3 significant digits (e.g. 2.18E-04).
- Target files: header of 8 "Label: ..." lines, then "X [s]" column header, then time + 8 muscles,
  RAW EMG, 1925.926 Hz, ~56 s, 5 reaches, exact-zero padding at the start and end.
- MVC files: one muscle, already an RMS envelope ("FilterSlidingRMS58"). NOT used in this project
  (MVC normalisation proved unreliable after stroke; all parameters here are MVC-free).
- The time column is rounded (3 digits); time is rebuilt from the sampling rate instead.
- Folder layout: <root>/Health_reaching/<id>/..., <root>/Stroke_reaching/<id>/...
  Stroke folders 7, 8, 9 are missing from the published data (10 patients, not 13).
- Some patients have only Target 1-6; one file is named "MVC Poterior Deltoid.csv" (typo).

Run:  python -m src.dataset --check    -> results/subjects.csv (fixed subject list) + data_check.csv
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal

from src.utils import load_config, results_dir, save_csv

MUSCLES = ["TRAP", "AD", "MD", "PD", "PEC", "INF", "BIC", "TRI"]
MUSCLE_NAMES = {"TRAP": "Trapezius", "AD": "Anterior deltoid", "MD": "Medial deltoid",
                "PD": "Posterior deltoid", "PEC": "Pectoralis major", "INF": "Infraspinatus",
                "BIC": "Biceps", "TRI": "Triceps"}
EMG_CHANNEL_TO_MUSCLE = {1: "TRAP", 2: "AD", 3: "MD", 4: "PD", 5: "PEC", 6: "INF", 7: "BIC", 8: "TRI"}


# ---------------------------------------------------------------------------- file reading
def label_to_muscle(label: str) -> str | None:
    """'R ANTERIOR DELTOID: EMG 2->TShift [Volts]' -> 'AD'. Tolerant of spelling/word order."""
    u = re.sub(r"[^A-Z ]", " ", str(label).upper())
    if "TRAP" in u:
        return "TRAP"
    if "DELT" in u:
        if "ANT" in u:
            return "AD"
        if "MED" in u or "MID" in u or "LAT" in u:
            return "MD"
        if "POST" in u:
            return "PD"
    for key, m in (("PEC", "PEC"), ("INFRA", "INF"), ("BICEP", "BIC"), ("TRICEP", "TRI")):
        if key in u:
            return m
    ch = re.search(r"EMG\s*(\d+)", str(label), re.I)
    return EMG_CHANNEL_TO_MUSCLE.get(int(ch.group(1))) if ch else None


@dataclass
class Recording:
    data: dict            # muscle -> 1-D array in microvolts
    fs: float             # Hz, from the file header
    is_envelope: bool     # True for the MVC files (already RMS)


def load_recording(path: Path, fs_fallback: float = 1925.926) -> Recording:
    with open(path, "r", encoding="utf-8-sig", errors="ignore") as fh:
        head = [fh.readline() for _ in range(60)]
    fs_vals = [float(m.group(1)) for line in head
               for m in [re.search(r"Sampling frequency:\s*([0-9.eE+\-]+)", line)] if m]
    fs = fs_vals[0] if fs_vals else fs_fallback
    hdr = next((i for i, line in enumerate(head) if line.lstrip().startswith("X [s]")), None)
    if hdr is None:
        raise ValueError(f"{path}: no 'X [s]' header line - not a Delsys export?")
    sep = max(["\t", ",", ";"], key=head[hdr].count)
    df = pd.read_csv(path, sep=sep, skiprows=hdr, encoding="utf-8-sig", low_memory=False)
    df = df.loc[:, [c for c in df.columns if not str(c).startswith("Unnamed") and str(c).strip()]]
    df = df.apply(pd.to_numeric, errors="coerce").dropna()
    data, env = {}, False
    for c in df.columns[1:]:                              # column 0 = rounded time, not used
        m = label_to_muscle(c)
        if m is None or m in data:
            continue
        data[m] = df[c].to_numpy(float) * 1e6              # V -> uV
        env = env or ("RMS" in str(c).upper())
    if not data:
        raise ValueError(f"{path}: no muscle column recognised in {list(df.columns)}")
    return Recording(data, fs, env)


# ---------------------------------------------------------------------------- subjects
@dataclass
class Subject:
    sid: str                                   # e.g. "H_1", "S_10"
    group: str                                 # "healthy" | "stroke"
    folder: Path
    target_files: dict = field(default_factory=dict)   # int target id -> Path


def discover_subjects(root: Path) -> list[Subject]:
    """Find every subject folder under Health_reaching / Stroke_reaching."""
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(f"Data folder not found: {root.resolve()} - see README 'Data'.")
    subjects = []
    for grp_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        name = grp_dir.name.lower()
        group = "healthy" if "health" in name else "stroke" if "stroke" in name else None
        if group is None:
            continue
        for sub in sorted(p for p in grp_dir.iterdir() if p.is_dir()):
            s = Subject(f"{group[0].upper()}_{sub.name}", group, sub)
            for f in sub.iterdir():
                m = re.match(r"target[_\s-]*(\d+)", f.stem, re.I)
                if m and f.is_file():
                    s.target_files[int(m.group(1))] = f
            if s.target_files:
                subjects.append(s)
    key = lambda s: (s.group != "healthy", int(re.sub(r"\D", "", s.sid) or 0))
    return sorted(subjects, key=key)


def common_targets(subjects: list[Subject]) -> list[int]:
    return sorted(set.intersection(*[set(s.target_files) for s in subjects]))


def subject_table(subjects: list[Subject]) -> pd.DataFrame:
    """The FIXED subject list. Leave-one-subject-out folds follow this order."""
    return pd.DataFrame([{"subject": s.sid, "group": s.group, "n_targets": len(s.target_files),
                          "targets": " ".join(map(str, sorted(s.target_files)))} for s in subjects])


# ---------------------------------------------------------------------------- signal processing
def clean_emg(x: np.ndarray, fs: float, cfg: dict) -> np.ndarray:
    """Remove offset, band-pass (default 20-450 Hz), notch 50 Hz. Zero-phase. x: (n,) or (n, k)."""
    s = cfg["signal"]
    x = x - np.mean(x, axis=0, keepdims=True)
    lo, hi = s["bandpass_hz"]
    sos = signal.butter(s["bandpass_order"], [lo, min(hi, 0.45 * fs)], btype="bandpass", fs=fs, output="sos")
    x = signal.sosfiltfilt(sos, x, axis=0)
    b, a = signal.iirnotch(s["notch_hz"], Q=s["notch_q"], fs=fs)
    return signal.filtfilt(b, a, x, axis=0)


def rms_envelope(x: np.ndarray, n: int) -> np.ndarray:
    """Sliding RMS over n samples (same as Delsys FilterSlidingRMS58 when n=58). x: (n,) or (n, k)."""
    k = np.ones(int(n)) / int(n)
    sq = x ** 2
    if sq.ndim == 1:
        return np.sqrt(np.convolve(sq, k, mode="same"))
    return np.sqrt(np.column_stack([np.convolve(sq[:, j], k, mode="same") for j in range(sq.shape[1])]))


def detect_movements(env: np.ndarray, fs: float, cfg: dict) -> list[tuple[int, int]]:
    """Find the reaches from all 8 envelopes together. Returns [(start, end), ...] sample indices.
    Tested: finds exactly 5 movements in Health_reaching/1/Target 1."""
    mv = cfg["movement"]
    scale = np.percentile(env, 99, axis=0)
    comb = (env / np.where(scale > 0, scale, 1.0)).sum(axis=1)
    k = max(1, int(mv["smooth_s"] * fs))
    comb = np.convolve(comb, np.ones(k) / k, mode="same")
    lo, hi = np.percentile(comb, 10), np.percentile(comb, 99)
    on = comb > lo + mv["threshold_frac"] * (hi - lo)
    idx = np.flatnonzero(np.diff(np.r_[0, on.astype(int), 0]))
    return [(int(a), int(b)) for a, b in zip(idx[::2], idx[1::2]) if (b - a) >= mv["min_duration_s"] * fs]


@dataclass
class Trial:
    """One Target file, ready for parameter computation."""
    subject: str
    group: str
    target: int
    fs: float
    emg: np.ndarray        # (n, 8) cleaned raw EMG, uV, columns in MUSCLES order
    env: np.ndarray        # (n, 8) 58-sample RMS envelope of `emg`
    movements: list        # [(start, end), ...]


def load_trial(subject: Subject, target: int, cfg: dict) -> Trial:
    """Load one Target file -> cropped (zero padding removed), cleaned, enveloped, movements found."""
    rec = load_recording(subject.target_files[target], cfg["data"]["fs_fallback"])
    missing = [m for m in MUSCLES if m not in rec.data]
    if missing:
        raise ValueError(f"{subject.sid} Target {target}: missing muscles {missing}")
    X = np.column_stack([rec.data[m] for m in MUSCLES])
    nz = np.flatnonzero(~np.all(X == 0, axis=1))
    X = X[nz[0]: nz[-1] + 1]                                   # crop zero padding
    emg = clean_emg(X, rec.fs, cfg)
    env = rms_envelope(emg, cfg["signal"]["envelope_rms_samples"])
    return Trial(subject.sid, subject.group, target, rec.fs, emg, env, detect_movements(env, rec.fs, cfg))


def main():
    ap = argparse.ArgumentParser(description="Write the fixed subject list and check every file loads.")
    ap.add_argument("--config", default="configs/base.yaml")
    ap.add_argument("--data", help="override paths.data_root")
    ap.add_argument("--check", action="store_true", help="also load every Target file and count movements")
    ap.add_argument("--tag", help="write to results/ablations/<tag>/ (e.g. fake)")
    a = ap.parse_args()
    cfg = load_config(a.config, {"paths.data_root": a.data} if a.data else None)
    subs = discover_subjects(Path(cfg["paths"]["data_root"]))
    tab = subject_table(subs)
    print(tab.groupby("group").size().rename("subjects").to_string())
    print("Targets done by every subject:", common_targets(subs))
    out = results_dir(cfg, a.tag)
    save_csv(tab, out / "subjects.csv")
    if a.check:
        rows = []
        for s in subs:
            for t in sorted(s.target_files):
                tr = load_trial(s, t, cfg)
                rows.append({"subject": s.sid, "target": t, "fs": round(tr.fs, 3),
                             "seconds": round(len(tr.emg) / tr.fs, 1), "n_movements": len(tr.movements)})
                if len(tr.movements) != cfg["data"]["expected_movements_per_target"]:
                    print(f"  [check] {s.sid} Target {t}: {len(tr.movements)} movements")
        save_csv(pd.DataFrame(rows), out / "data_check.csv")


if __name__ == "__main__":
    main()
