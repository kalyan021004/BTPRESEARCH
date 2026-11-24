"""
Make a SMALL FAKE dataset in exactly the same file format as the real Mendeley data, so the pipeline
can be developed and tested without the real files (e.g. by Claude Code in the cloud).

FAKE SIGNALS - never report anything computed from them.

    python scripts/make_fake_data.py                     # -> data/fake/EMG_Reaching_Healthy_Stroke
    python scripts/make_fake_data.py --healthy 4 --stroke 4
"""
import argparse
from pathlib import Path

import numpy as np
from scipy import signal

FS = 1925.926
LABELS = ["R TRAPEZIUS MIDDLE FIBERS: EMG 1", "R ANTERIOR DELTOID: EMG 2", "R MEDIAL DELTOID : EMG 3",
          "R POSTERIOR DELTOID: EMG 4", "R PECTORALIS MAJOR: EMG 5", "R INFRASPINATIS: EMG 6",
          "R BICEPS BRACHII: EMG 7", "R TRICEPS BRACHII: EMG 8"]
MVC_NAMES = ["Upper Trapezius", "Anterior Deltoid", "Medial Deltoid", "Posterior Deltoid",
             "Pectoralis Major", "Infraspinatus", "Biceps", "Triceps"]


def noise(n, rng):
    sos = signal.butter(3, [30, 250], btype="bandpass", fs=FS, output="sos")
    x = signal.sosfilt(sos, rng.standard_normal(n + 500))[500:]
    return x / x.std()


def write_target(path, X):
    n = len(X)
    head = [f"Label: {lab}->TShift Sampling frequency: 1.925926e+003 Number of points: {n} "
            f"X start: 0.000000e+000 Unit: Volts Domain Unit: s" + "\t" * 8 for lab in LABELS]
    head.append("X [s]\t" + "\t".join(f"{lab}->TShift [Volts]" for lab in LABELS))
    t = np.arange(n) / FS
    np.savetxt(path, np.column_stack([t, X]), fmt="%.2E", delimiter="\t", header="\n".join(head), comments="")


def write_mvc(path, label, env):
    n = len(env)
    lab = f"{label}->filter (FilterSlidingRMS58)"
    head = [f"Label: {lab} Sampling frequency: 1.925926e+003 Number of points: {n} X start: 0.000000e+000 "
            "Unit: Volts Domain Unit: s\t"] + [f"{k}\t" for k in (
        "Start Trigger Method: None", "Stop Trigger Method: None", "Use Camera: NO", "Video File Path: ",
        "System Gain: 3.000000e+002", "A/D card Gain: 1.000000e+000", "Bit Resolution: -1.000000e+000",
        "Bias: 0.000000e+000", "High pass cutoff frequency: 0.000000e+000",
        "Low pass cutoff frequency: 0.000000e+000")] + [f"X [s]\t{lab} [Volts]"]
    np.savetxt(path, np.column_stack([np.arange(n) / FS, env]), fmt="%.2E", delimiter="\t",
               header="\n".join(head), comments="")


def subject(folder: Path, stroke: bool, targets, rng):
    folder.mkdir(parents=True, exist_ok=True)
    gain = rng.lognormal(0, 0.3, 8) * 100e-6                     # volts
    pref = rng.uniform(0, 2 * np.pi, 8)
    for t in targets:
        ang = (t - 1) / 9 * 2 * np.pi
        move_s = rng.normal(2.2 if stroke else 1.6, 0.15)
        pad, rest = int(0.5 * FS), int(0.8 * FS)
        mv = int(move_s * FS)
        n = 2 * pad + 5 * (rest + mv)
        env = np.full((n, 8), 0.03)
        for r in range(5):
            s0 = pad + rest + r * (rest + mv)
            tt = np.linspace(0, 1, mv)
            for c in range(8):
                tuning = (0.25 if stroke else 0.7) * np.cos(ang - pref[c])
                amp = max(0.05, 0.5 * (1 + tuning)) * rng.normal(1, 0.25 if stroke else 0.08)
                shape = np.sin(np.pi * tt) ** 2
                if stroke:                                       # fragmented: extra sub-bursts
                    shape = shape * (0.6 + 0.4 * np.abs(np.sin(3 * np.pi * tt + rng.uniform(0, 1))))
                env[s0:s0 + mv, c] += amp * shape
        X = np.column_stack([gain[c] * env[:, c] * noise(n, rng) for c in range(8)])
        X[:pad] = 0
        X[-pad:] = 0
        write_target(folder / f"Target {t}.csv", X)
    for c in range(8):
        m = int(6 * FS)
        e = np.full(m, 5e-6)
        a0, a1 = int(1 * FS), int(4 * FS)
        e[a0:a1] += gain[c] * np.hanning(a1 - a0)
        write_mvc(folder / f"MVC {MVC_NAMES[c]}.csv", LABELS[c], e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/fake/EMG_Reaching_Healthy_Stroke")
    ap.add_argument("--healthy", type=int, default=4)
    ap.add_argument("--stroke", type=int, default=4)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    root = Path(a.out)
    for i in range(1, a.healthy + 1):
        subject(root / "Health_reaching" / str(i), False, range(1, 10), rng)
    for i in range(1, a.stroke + 1):                             # some patients did only 6 targets
        subject(root / "Stroke_reaching" / str(i), True, range(1, 7 if i % 2 else 10), rng)
    print(f"FAKE data written to {root.resolve()}")


if __name__ == "__main__":
    main()
