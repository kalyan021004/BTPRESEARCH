# Progress

Deadline: BTP report and presentation in **2 days**.
Plan: Day 1 = stages 1-4 (on fake data in the cloud, then real data on the PC). Day 2 = stages 5-7.

## 1. Setup
- [ ] Repo pushed to GitHub; `pip install -r requirements.txt` works
- [ ] Fake data generated (`python scripts/make_fake_data.py`)

## 2. Data
- [x] Real data placed in `data/raw/EMG_Reaching_Healthy_Stroke` (on the PC)
- [x] `python -m src.dataset --check` on real data: 12 healthy, 10 stroke; note every `[check]` line here
  - Result (2026-11-24): healthy 12, stroke 10; targets done by every subject: [1, 2, 3, 4, 5, 6].
    189 files load; fs = 1925.926 Hz in all; cropped length 55.0-55.2 s; H_1 Target 1 = 5 movements.
  - 184 / 189 files give 5 movements; 5 files give 6 (all stroke, all within targets 1-6):
    ```
    [check] S_12 Target 3: 6 movements
    [check] S_12 Target 5: 6 movements
    [check] S_13 Target 2: 6 movements
    [check] S_13 Target 3: 6 movements
    [check] S_13 Target 4: 6 movements
    ```
  - Decision: thresholds not changed (no tuning); robustness is shown by the `threshold_low/high` ablations.
    Full per-file table in `results/data_check.csv`.
- [x] `results/subjects.csv` committed (fixed subject order = leave-one-out folds): H_1-H_12, then S_1-S_6, S_10-S_13

## 3. Baseline parameters (simple, timing-based)
- [x] P3 movement duration (worked example)
- [x] P1 fragmentation
  - Low-pass order added to config (`lowpass_order: 4`, as the docstring already said). Check: 1 / 2 / 1-with-noise bursts -> 1 / 2 / 1 peaks; fake data 8 rows per trial, n = 5, no NaN.
- [x] P2 repetition consistency
  - Flat (zero-variance) curves are dropped before r and `n` counts the curves used. Check: identical / alternating / noise -> 1.00 / 0.19 / 0.00; 1 movement -> NaN. Fake: r about 0.73-0.76, no NaN.
- [ ] P8 agonist-antagonist correlation
- [ ] P9 direction tuning depth

## 4. Main parameters (signal statistics and coordination)
- [ ] P4 median frequency
- [ ] P5 kurtosis
- [ ] P6 sample entropy (check: white noise about 2.2, sine about 0)
- [ ] P7 intermuscular beta coherence
- [ ] P10 one-synergy VAF
- [ ] `to_subject_level()` + split-half tables in `src/extract.py`
- [ ] Full extract on real data; `results/parameters_*.csv` committed

## 5. Ablations (robustness)
- [ ] `--ablation threshold_low` and `threshold_high` (movement detection)
- [ ] `--ablation no_rectify` (coherence without rectification)
- [ ] Sensitivity check excluding the 5 flagged files (S_12 T3/T5, S_13 T2/T3/T4)
- [ ] Short table: does the list of significant parameters change?

## 6. Evaluation
- [ ] Group comparison (primary table, FDR) and per-muscle secondary table
- [ ] Split-half reliability (ICC, MDC)
- [ ] Correlation between parameters (redundancy)
- [ ] Leave-one-subject-out composite score (AUC, CI, permutation p, selection stability)
- [ ] `summary.json` with every number the report quotes

## 7. Report and presentation
- [ ] `src/make_report_assets.py`: figures 1-5, tables 1-3, numbers.md
- [ ] BTP report written from `report/outline.md` (numbers only from report/generated/)
- [ ] Slides (about 10) from the same figures
- [ ] Limitations section: n = 22, no clinical scores, ages not reported, crosstalk,
      split reaches in flagged files may partly reflect real fragmentation

## Decisions log
- MVC files are not used: the MVC was unreliable after stroke (33 % vs 6 % exceedance, earlier analysis).
- Only directions 1-6 are used (done by every subject).
- No train/val/test split (22 subjects): group statistics on all subjects; the composite uses leave-one-subject-out.
- Movement detection rule kept unchanged (2026-11-24). 5 of 189 files flagged with 6 movements, all
  stroke (S_12, S_13); inspected in figures/check/ (diagnostic plots, not committed).
  3 are reaches split by a short dip (S_13 T3, S_13 T4, S_12 T5); 2 are extra non-reach activations
  (S_13 T2, S_12 T3). Main results use all files; a sensitivity check excludes these 5 files (stage 5).
  Limitation: split reaches may partly reflect real fragmentation, not only a detection error.
