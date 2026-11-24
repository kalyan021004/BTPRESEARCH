# Progress

Deadline: BTP report and presentation in **2 days**.
Plan: Day 1 = stages 1-4 (on fake data in the cloud, then real data on the PC). Day 2 = stages 5-7.

## 1. Setup
- [ ] Repo pushed to GitHub; `pip install -r requirements.txt` works
- [ ] Fake data generated (`python scripts/make_fake_data.py`)

## 2. Data
- [ ] Real data placed in `data/raw/EMG_Reaching_Healthy_Stroke` (on the PC)
- [ ] `python -m src.dataset --check` on real data: 12 healthy, 10 stroke; note every `[check]` line here
- [ ] `results/subjects.csv` committed (fixed subject order = leave-one-out folds)

## 3. Baseline parameters (simple, timing-based)
- [x] P3 movement duration (worked example)
- [ ] P1 fragmentation
- [ ] P2 repetition consistency
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
- [ ] Limitations section: n = 22, no clinical scores, ages not reported, crosstalk, 3-digit data export

## Decisions log
- MVC files are not used: the MVC was unreliable after stroke (33 % vs 6 % exceedance, earlier analysis).
- Only directions 1-6 are used (done by every subject).
- No train/val/test split (22 subjects): group statistics on all subjects; the composite uses leave-one-subject-out.
