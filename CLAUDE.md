# Instructions for Claude Code

## Goal
Find statistical EMG parameters that clearly separate post-stroke patients (n = 10) from healthy people
(n = 12) during reaching. All parameters must be **MVC-free**. Deliverables: a BTP report and slides,
**due within 2 days**. Choose the simplest correct solution; do not add features nobody asked for.

## Background (already done in an earlier project - do not redo)
- A normative baseline was built using %MVC effort, co-activation and direction tuning, plus ML
  classification (healthy-only one-class SVM AUC 0.98, supervised AUC 0.96-0.99). The supervisor said
  this kind of work is common, so this project focuses on **new parameters**.
- Key earlier finding: reaching exceeded the MVC in 33 % of stroke vs 6 % of healthy muscle values
  (p = 0.007). That is why nothing here uses the MVC files.

## The data (read the docstring of src/dataset.py first)
- The real data is NOT in the repo (data/ is in .gitignore). In the cloud, use the fake data:
  `python scripts/make_fake_data.py`, then add `--data data/fake/EMG_Reaching_Healthy_Stroke --tag fake`
  to every command. The user runs the real data on their Windows PC and commits `results/`.
- `src/dataset.py` is tested on real files (it finds exactly 5 reaches in Healthy 1 / Target 1).
  Do not rewrite it. Extend it only if you must, and keep it backwards compatible.
- Use only reach directions done by every subject (1-6), via `common_targets()`.

## Dataset format (verified on the real files, 2026-11-24)
- Source: Mendeley, Israely, Leisman & Carmeli 2019 (DOI 10.17632/f4hh43nd78.2).
- Layout: `<root>/Health_reaching/<1-12>/` and `<root>/Stroke_reaching/<1-6,10-13>/`.
  **12 healthy, 10 stroke** (stroke folders 7, 8, 9 do not exist). 365 files, all `.csv`.
- Per subject: `Target 1..9.csv` + 8 `MVC <muscle>.csv` (MVC not used).
  Stroke 3, 6, 13 have only Target 1-6 -> 189 target files.
  Stroke 10 uses lowercase `target N.csv`; MVC file names have typos/variants (e.g. "Poterior", "Upper Traps").
- Main analysis uses target directions 1-6, common to all 22 subjects.
- Target file format (Delsys EMGworks text export, all 189 files identical in structure):
  - Lines 1-8: `Label: R <MUSCLE>: EMG <n>->TShift Sampling frequency: 1.925926e+003 Number of points: ... Unit: Volts`
  - Line 9: column header `X [s],<8 channel labels>`; then data rows. **Comma-separated**, CRLF.
  - 9 columns: time (s) + 8 channels of **raw EMG in volts**, scientific notation, 7 significant digits.
  - Exact-zero padding at the start and end of each file.
- Sampling rate: **1925.926 Hz** in every target file. Duration 55-56 s (~108 700 samples), 5 reaches per file.
- Channels (same in all files, all right side "R"):
  EMG1 Trapezius (middle fibers) = TRAP, EMG2 Anterior deltoid = AD, EMG3 Medial deltoid = MD,
  EMG4 Posterior deltoid = PD, EMG5 Pectoralis major = PEC, EMG6 Infraspinatus = INF,
  EMG7 Biceps brachii = BIC, EMG8 Triceps brachii = TRI.
- Trapezius naming: the target files label EMG1 "TRAPEZIUS MIDDLE FIBERS", but most MVC file names
  say "Upper Trapezius" (variants: "Trapezius", "Upper Traps").
- MVC files: one channel, already an RMS envelope (`FilterSlidingRMS<N>`, N varies 16-82 between files).

## Folder rules
- `configs/base.yaml` holds every threshold and setting. Never hard-code a number in `src/`.
- `src/parameters.py`: one function per parameter. Follow the recipe in each docstring exactly.
- **Save every result to `results/` as CSV or JSON.** Nothing is only printed.
- Figures go to `figures/`, generated tables go to `report/generated/`, and both are made only by
  `src/make_report_assets.py`, reading only from `results/` and the config.
- **Never hard-code numbers in the report or slides.** Quote them from `report/generated/numbers.md`
  or the generated tables. If a number is missing, add it to `summary.json` in `src/evaluate.py`.
- Do not add new top-level folders or files unless PROGRESS.md needs them.

## Statistics rules (these protect the validity of the results)
- The **subject** is the unit of analysis. Never use movements, windows or targets as independent samples.
- The 10 primary parameters and their aggregation rule are **fixed in advance**. If you add an
  exploratory parameter, label it "exploratory" in every table and keep it out of the FDR family.
- All tests are two-sided Mann-Whitney U with Benjamini-Hochberg FDR across the 10 primary parameters.
  Always report an effect size (Cliff's delta, AUC) with a bootstrap 95 % CI next to every p-value.
- Composite score: feature selection happens **inside** each leave-one-subject-out fold. Never select
  on all data first.
- Report negative and null results too. Do not tune thresholds to make a parameter "work". Use the
  `ablations` in the config to show robustness instead.

## Coding style
- Python 3.10+, numpy / scipy / pandas / scikit-learn / matplotlib only.
- Run modules as `python -m src.<name>`. Paths via `pathlib`, so they work on Windows too.
- Short functions with a docstring giving the unit of the returned value. Comments only where the
  reason is not obvious.
- Random seed from the config via `utils.set_seed()`. Pass the returned Generator around; never call
  np.random directly.
- Return NaN (never crash) for not-enough-data cases, and record `n` in the output.
- Test each new parameter on a simple known signal (e.g. sample entropy of white noise is about 2.2)
  and on the fake data before marking it done.

## Workflow
1. Pick the next unchecked item in PROGRESS.md.
2. Implement it, run it on the fake data, and check the output CSV looks sensible.
3. Tick the box in PROGRESS.md and add a one-line note (what changed, any decision made).
4. Commit with a clear message. Never commit `data/`.
