# MVC-free statistical EMG parameters: healthy vs post-stroke reaching

**BTP project, IIIT Sri City.** Output: BTP report and presentation.

## What this project does

We design and test **10 statistical parameters** that describe *how* muscles are activated during
reaching. Then we check which of them clearly separate **post-stroke patients** from **healthy people**.

Every parameter is **MVC-free**: it is calculated from the reaching EMG alone, without the maximum
voluntary contraction (MVC) test. We need this because our earlier analysis of the same data found
that the MVC "maximum" is unreliable after stroke. During ordinary reaching, muscle activity went
above it in 33 % of patient muscle values, but only 6 % of healthy ones.

| # | Parameter | Plain meaning | Expected in stroke |
|---|---|---|---|
| P1 | Activation fragmentation | bursts per muscle per reach (jerky vs smooth) | higher |
| P2 | Repetition consistency | how alike the 5 repeats of a reach are | lower |
| P3 | Movement duration | how long each reach takes | higher |
| P4 | Median frequency | "pitch" of the EMG | either |
| P5 | Amplitude kurtosis | how peaked the EMG distribution is (motor-unit recruitment) | either |
| P6 | Sample entropy | complexity / irregularity of the EMG | lower |
| P7 | Intermuscular beta coherence | shared 15-30 Hz drive between muscles | either |
| P8 | Agonist-antagonist correlation | opposing muscles rising together (co-activation) | higher |
| P9 | Direction tuning depth | how much a muscle adapts to reach direction | lower |
| P10 | One-synergy VAF | how much one "muscle team" explains everything | higher |

For each parameter we report:
- **Group difference:** Mann-Whitney test, Cliff's delta, AUC, each with a 95 % CI, plus FDR correction.
- **Reliability:** split-half ICC within each subject.
- **Redundancy:** correlation with the other parameters.

Finally, a **leave-one-subject-out composite** score combines the 3 strongest parameters.

## Data

Israely, Leisman & Carmeli (2019), *EMG datasets from hand-reaching movements for multiple directions of
healthy and post-stroke individuals*, Mendeley Data, DOI 10.17632/f4hh43nd78.2 (CC BY 4.0).

- 12 healthy people and 10 stroke patients (stroke folders 7-9 are missing from the published data).
- 8 muscles, 1925.926 Hz, 9 reach directions × 5 reaches. Some patients did only directions 1-6.

Put the unzipped folder here (this path is **not** pushed to GitHub):

```
data/raw/EMG_Reaching_Healthy_Stroke/
    Health_reaching/1 ... 12/
    Stroke_reaching/1 ... 13/
```

## Setup and run (Windows PowerShell or Linux)

```bash
pip install -r requirements.txt

python -m src.dataset --check          # 1. fixed subject list + checks every file finds 5 reaches
python -m src.extract                  # 2. all parameters for every subject  -> results/
python -m src.evaluate                 # 3. statistics                        -> results/
python -m src.make_report_assets       # 4. tables + figures                  -> report/generated/, figures/
```

Without the real data (for development), use the fake data, which has the same file format:

```bash
python scripts/make_fake_data.py
python -m src.dataset --data data/fake/EMG_Reaching_Healthy_Stroke --check --tag fake
python -m src.extract --data data/fake/EMG_Reaching_Healthy_Stroke --tag fake
python -m src.evaluate --tag fake
python -m src.make_report_assets --tag fake
```

Sensitivity checks: `python -m src.extract --ablation threshold_low` (see `ablations:` in `configs/base.yaml`).

## Folder structure

```
configs/base.yaml          every setting and threshold (single source of truth)
src/dataset.py             reading the Delsys files, cleaning, finding the reaches  [done, tested]
src/parameters.py          the 10 parameters                                         [P3 done, rest TODO]
src/extract.py             runs the parameters for every subject -> results/        [loop done, tables TODO]
src/evaluate.py            statistics, reliability, composite score                  [TODO]
src/make_report_assets.py  tables + figures from results/ only                       [TODO]
src/utils.py               config, seeds, saving                                     [done]
scripts/make_fake_data.py  fake data in the real file format                         [done]
results/                   every number, as CSV / JSON (pushed to GitHub)
figures/                   PNG figures (pushed)
report/outline.md          report + slide plan; report/generated/ holds the auto-made tables
```

## Status

See `PROGRESS.md`.
