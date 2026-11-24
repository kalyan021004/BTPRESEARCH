"""
The 10 PRIMARY statistical parameters (the "model" of this project).

All are MVC-FREE: computed from the raw reaching EMG only. Reason: in our previous analysis reaching
activity exceeded the MVC "maximum" in 33 % of stroke muscle values vs 6 % in healthy (p = 0.007),
so MVC normalisation is unreliable after stroke. Every parameter here is either scale-free or a time /
frequency / shape measure, so electrode gain and skin do not matter.

Each function returns a list of rows:
    {"parameter": "P1_fragmentation", "muscle": "BIC" | "ALL" | "BIC-TRI",
     "target": 3 | "ALL", "value": float, "n": number of movements or windows used}
Settings come from cfg["parameters"][<name>] - never hard-code thresholds.

Rules for every function (see CLAUDE.md):
- Use only samples inside trial.movements (the 5 reaches), never the rest periods.
- Return NaN (not an error) when there is not enough data, and keep "n" honest.
- Add a docstring line stating the unit.

P3 is implemented as a worked example of the pattern. The other 9 are TODO.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
from scipy.stats import kurtosis
from sklearn.decomposition import NMF
from scipy.signal import butter, find_peaks, csd, sosfiltfilt, welch

from src.dataset import MUSCLES, Trial


def _row(param: str, muscle: str, target, value: float, n: int) -> dict:
    return {"parameter": param, "muscle": muscle, "target": target, "value": float(value), "n": int(n)}


def segments(trial: Trial, which: str = "emg") -> list[np.ndarray]:
    """List of (len, 8) arrays, one per movement. which = 'emg' (cleaned raw) or 'env' (envelope)."""
    X = trial.emg if which == "emg" else trial.env
    return [X[a:b] for a, b in trial.movements]


def active_windows(trial: Trial, j: int, window_s: float, min_env_frac: float) -> list[np.ndarray]:
    """Non-overlapping windows (cleaned raw EMG, uV) of muscle j inside the movements, kept only if the
    window's mean envelope >= min_env_frac * that movement's envelope maximum. Used by P5 and P6."""
    w = int(round(window_s * trial.fs))
    out = []
    for a, b in trial.movements:
        x, e = trial.emg[a:b, j], trial.env[a:b, j]
        if w < 2 or len(x) < w or e.max() <= 0:
            continue
        for k in range(len(x) // w):
            if e[k * w:(k + 1) * w].mean() >= min_env_frac * e.max():
                out.append(x[k * w:(k + 1) * w])
    return out


# ============================================================================ per trial, per muscle
def p1_fragmentation(trial: Trial, cfg: dict) -> list[dict]:
    """P1 Activation fragmentation - unit: peaks per movement. Expected: higher in stroke.

    TODO: implement.
    For each muscle j and each movement:
      1. env = envelope segment of muscle j; low-pass it (4th-order Butterworth, zero-phase,
         cutoff cfg[...]["lowpass_hz"] = 6 Hz).
      2. count peaks with scipy.signal.find_peaks(prominence = min_prominence_frac * max(env)).
    value = mean peak count over the movements of this trial. One row per muscle.
    Meaning: a smooth reach has 1-2 bursts per muscle; a fragmented, jerky reach has more.
    """
    c = cfg["parameters"]["P1_fragmentation"]
    sos = butter(c["lowpass_order"], c["lowpass_hz"], fs=trial.fs, output="sos")
    min_len = 3 * (2 * sos.shape[0] + 1)          # sosfiltfilt default padlen + 1
    rows = []
    for j, m in enumerate(MUSCLES):
        counts = []
        for seg in segments(trial, "env"):
            if len(seg) <= min_len:
                continue
            x = sosfiltfilt(sos, seg[:, j])
            if not np.isfinite(x).all() or x.max() <= 0:
                continue
            peaks, _ = find_peaks(x, prominence=c["min_prominence_frac"] * x.max())
            counts.append(len(peaks))
        rows.append(_row("P1_fragmentation", m, trial.target, np.mean(counts) if counts else np.nan, len(counts)))
    return rows


def p2_repetition_consistency(trial: Trial, cfg: dict) -> list[dict]:
    """P2 Repetition consistency - unit: mean Pearson r (-1..1). Expected: lower in stroke.

    TODO: implement.
    For each muscle j:
      1. take the envelope of muscle j in each movement; resample each to n_points (101) with
         np.interp so all movements have the same length (time-normalised 0-100 %).
      2. Pearson r for every pair of movements; value = mean r. Needs >= 2 movements, else NaN.
    Meaning: how similar the muscle's activation pattern is across the 5 repeats of the same reach.
    """
    npts = cfg["parameters"]["P2_repetition_consistency"]["n_points"]
    grid = np.linspace(0, 1, npts)
    segs = [s for s in segments(trial, "env") if len(s) >= 2]
    rows = []
    for j, m in enumerate(MUSCLES):
        curves = np.array([np.interp(grid, np.linspace(0, 1, len(s)), s[:, j]) for s in segs]).reshape(-1, npts)
        curves = curves[curves.std(axis=1) > 0]             # a flat curve has no defined r
        if len(curves) < 2:
            rows.append(_row("P2_repetition_consistency", m, trial.target, np.nan, len(curves)))
            continue
        r = np.corrcoef(curves)[np.triu_indices(len(curves), k=1)]
        rows.append(_row("P2_repetition_consistency", m, trial.target, r.mean(), len(curves)))
    return rows


def p4_median_frequency(trial: Trial, cfg: dict) -> list[dict]:
    """P4 Median frequency - unit: Hz. Expected: two-sided (literature mixed).

    TODO: implement.
    For each muscle j: Welch PSD (nperseg from config, Hann, 50 % overlap) of the CLEANED RAW EMG in
    each movement; average the PSDs over movements (weight by segment count); keep 20-450 Hz;
    value = frequency where the cumulative power reaches 50 %.
    Note in the report: dynamic contractions; MDF also changes with force level.
    """
    nper = cfg["parameters"]["P4_median_frequency"]["welch_nperseg"]
    lo, hi = cfg["signal"]["bandpass_hz"]
    segs = [s for s in segments(trial, "emg") if len(s) >= nper]
    rows = []
    for j, m in enumerate(MUSCLES):
        psd_sum, k_sum, f = 0.0, 0, None
        for s in segs:
            f, pxx = welch(s[:, j], fs=trial.fs, nperseg=nper)     # Hann, 50 % overlap (scipy default)
            k = (len(s) - nper) // (nper // 2) + 1                   # number of Welch segments
            psd_sum, k_sum = psd_sum + k * pxx, k_sum + k
        if not k_sum:
            rows.append(_row("P4_median_frequency", m, trial.target, np.nan, 0))
            continue
        band = (f >= lo) & (f <= hi)
        cum = np.cumsum(psd_sum[band])
        val = f[band][np.searchsorted(cum, 0.5 * cum[-1])] if cum[-1] > 0 else np.nan
        rows.append(_row("P4_median_frequency", m, trial.target, val, len(segs)))
    return rows


def p5_kurtosis(trial: Trial, cfg: dict) -> list[dict]:
    """P5 Amplitude kurtosis - unit: excess kurtosis (0 for a Gaussian). Expected: two-sided.

    TODO: implement.
    For each muscle j:
      1. split each movement of the CLEANED RAW EMG into non-overlapping windows of window_s (0.1 s);
      2. keep windows whose mean envelope >= min_envelope_frac (0.5) * the movement's envelope max
         (so we compare similar activation levels and avoid amplitude changes inflating kurtosis);
      3. scipy.stats.kurtosis(window, fisher=True) per window; value = mean over kept windows; n = windows.
    Meaning: sEMG is close to Gaussian when many motor units are active; fewer / larger / synchronised
    units make it more peaked (higher kurtosis).
    """
    c = cfg["parameters"]["P5_kurtosis"]
    rows = []
    for j, m in enumerate(MUSCLES):
        k = [kurtosis(x, fisher=True) for x in active_windows(trial, j, c["window_s"], c["min_envelope_frac"])]
        k = [v for v in k if np.isfinite(v)]
        rows.append(_row("P5_kurtosis", m, trial.target, np.mean(k) if k else np.nan, len(k)))
    return rows


def p6_sample_entropy(trial: Trial, cfg: dict) -> list[dict]:
    """P6 Sample entropy - unit: dimensionless. Expected: lower in stroke.

    TODO: implement.
    Same window selection as P5 but window_s = 0.25 s. For each kept window x:
      SampEn(m, r) with m = 2, r = r_frac * std(x)  (r_frac = 0.2), Chebyshev distance,
      SampEn = -ln(A / B), A = matches of length m+1, B = matches of length m (exclude self-matches).
      Write a vectorised numpy version (no external entropy package); return NaN if A == 0.
    value = mean over kept windows. Check on white noise (~2.2 for m=2, r=0.2) and a sine (~0).
    Note: the files store 7 significant digits, so quantisation does not limit entropy here.
    """
    raise NotImplementedError


# ============================================================================ per trial
def p3_movement_duration(trial: Trial, cfg: dict) -> list[dict]:
    """P3 Movement duration - unit: s. Expected: higher in stroke.   (IMPLEMENTED - worked example)

    Duration of each detected movement; value = mean over the movements of this trial.
    """
    d = [(b - a) / trial.fs for a, b in trial.movements]
    return [_row("P3_movement_duration", "ALL", trial.target, np.mean(d) if d else np.nan, len(d))]


def p8_antagonist_correlation(trial: Trial, cfg: dict) -> list[dict]:
    """P8 Agonist-antagonist envelope correlation - unit: Pearson r. Expected: higher in stroke.

    TODO: implement.
    For each pair in cfg[...]["pairs"] (BIC-TRI, AD-PD) and each movement: Pearson r between the two
    envelopes; value = mean r over movements. One row per pair, muscle = "BIC-TRI" / "AD-PD".
    Meaning: MVC-free co-activation - do opposing muscles rise and fall together?
    """
    rows = []
    for a, b in cfg["parameters"]["P8_antagonist_correlation"]["pairs"]:
        ia, ib = MUSCLES.index(a), MUSCLES.index(b)
        rs = [np.corrcoef(s[:, ia], s[:, ib])[0, 1] for s in segments(trial, "env")
              if len(s) >= 2 and s[:, ia].std() > 0 and s[:, ib].std() > 0]
        rows.append(_row("P8_antagonist_correlation", f"{a}-{b}", trial.target,
                         np.mean(rs) if rs else np.nan, len(rs)))
    return rows


# ============================================================================ per subject (all trials)
def p7_beta_coherence(trials: list[Trial], cfg: dict) -> list[dict]:
    """P7 Intermuscular beta coherence - unit: magnitude-squared coherence (0..1). Expected: two-sided.

    TODO: implement.
    For each of the 28 muscle pairs:
      1. signal = cleaned raw EMG, full-wave rectified if cfg rectify is true (common practice);
      2. for EVERY movement of EVERY trial compute Welch auto-spectra Pxx, Pyy and cross-spectrum Pxy
         (scipy.signal.csd / welch, nperseg 512, Hann, 50 % overlap) and SUM them over movements
         (pooling spectra, not averaging coherences);
      3. coherence = |Pxy|^2 / (Pxx * Pyy); value = mean over band_hz (15-30 Hz).
    Rows: one per pair (muscle = "AD-MD"), target = "ALL", n = number of Welch segments pooled.
    Limitation to report: crosstalk between neighbouring muscles (e.g. deltoid heads) raises coherence.
    """
    c = cfg["parameters"]["P7_beta_coherence"]
    nper, (lo, hi) = c["nperseg"], c["band_hz"]
    pairs = list(combinations(range(len(MUSCLES)), 2))
    Pauto, Pcross, k_sum, f = 0.0, {pr: 0.0 for pr in pairs}, 0, None
    for tr in trials:
        for s in segments(tr, "emg"):
            if len(s) < nper:
                continue
            x = np.abs(s) if c["rectify"] else s
            k = (len(x) - nper) // (nper // 2) + 1                   # Welch segments (Hann, 50 % overlap)
            f, pa = welch(x, fs=tr.fs, nperseg=nper, axis=0)         # (freqs, 8)
            Pauto = Pauto + k * pa
            for a, b in pairs:
                Pcross[(a, b)] = Pcross[(a, b)] + k * csd(x[:, a], x[:, b], fs=tr.fs, nperseg=nper)[1]
            k_sum += k
    rows = []
    for a, b in pairs:
        name = f"{MUSCLES[a]}-{MUSCLES[b]}"
        if not k_sum:
            rows.append(_row("P7_beta_coherence", name, "ALL", np.nan, 0))
            continue
        band = (f >= lo) & (f <= hi)
        with np.errstate(divide="ignore", invalid="ignore"):
            coh = np.abs(Pcross[(a, b)]) ** 2 / (Pauto[:, a] * Pauto[:, b])
        rows.append(_row("P7_beta_coherence", name, "ALL", np.nanmean(coh[band]) if np.isfinite(coh[band]).any() else np.nan, k_sum))
    return rows


def p9_direction_tuning(trials: list[Trial], cfg: dict) -> list[dict]:
    """P9 Direction tuning depth - unit: (max - min) / mean, scale-free. Expected: lower in stroke.

    TODO: implement.
    For each muscle: a_t = mean envelope during the movements of target t;
    value = (max_t a_t - min_t a_t) / mean_t a_t over the targets in `trials`. Needs >= 2 targets.
    Rows: one per muscle, target = "ALL". (Replaces the %MVC tuning from the earlier analysis.)
    """
    # a[t, j] = mean envelope of muscle j over all movement samples of target t
    a = np.array([np.concatenate(segs).mean(axis=0) for tr in trials if (segs := segments(tr, "env"))])
    rows = []
    for j, m in enumerate(MUSCLES):
        col = a[:, j] if a.size else np.array([])
        ok = len(col) >= 2 and col.mean() > 0
        val = (col.max() - col.min()) / col.mean() if ok else np.nan
        rows.append(_row("P9_direction_tuning", m, "ALL", val, len(col)))
    return rows


def p10_synergy_vaf1(trials: list[Trial], cfg: dict) -> list[dict]:
    """P10 One-synergy VAF - unit: fraction 0..1. Expected: higher in stroke.

    TODO: implement.
      1. concatenate the envelopes of all movements of all trials -> (n, 8);
      2. resample to resample_hz (100 Hz) by averaging consecutive samples;
      3. divide each muscle by its own maximum (scale-free);
      4. sklearn NMF(n_components=1, init="nndsvda", random_state=cfg["seed"], max_iter=1000);
         VAF = 1 - sum((E - W H)^2) / sum(E^2).
    Rows: one row, muscle = "ALL", target = "ALL".
    Meaning: how much of all muscle activity one single "muscle team" explains; high = less independent
    control of muscles.
    """
    segs = [s for tr in trials for s in segments(tr, "env")]
    if not segs:
        return [_row("P10_synergy_vaf1", "ALL", "ALL", np.nan, 0)]
    E = np.concatenate(segs)
    step = max(1, int(round(trials[0].fs / cfg["parameters"]["P10_synergy_vaf1"]["resample_hz"])))
    nb = len(E) // step
    E = E[: nb * step].reshape(nb, step, E.shape[1]).mean(axis=1)    # average consecutive samples
    mx = E.max(axis=0) if nb else np.zeros(E.shape[1])
    if nb < 2 or (mx <= 0).any():
        return [_row("P10_synergy_vaf1", "ALL", "ALL", np.nan, nb)]
    E = np.clip(E / mx, 0, None)
    nmf = NMF(n_components=1, init="nndsvda", random_state=cfg["seed"],
              max_iter=cfg["parameters"]["P10_synergy_vaf1"]["nmf_max_iter"])
    W = nmf.fit_transform(E)
    vaf = 1 - np.sum((E - W @ nmf.components_) ** 2) / np.sum(E ** 2)
    return [_row("P10_synergy_vaf1", "ALL", "ALL", vaf, nb)]


PER_TRIAL = [p1_fragmentation, p2_repetition_consistency, p3_movement_duration, p4_median_frequency,
             p5_kurtosis, p6_sample_entropy, p8_antagonist_correlation]
PER_SUBJECT = [p7_beta_coherence, p9_direction_tuning, p10_synergy_vaf1]
