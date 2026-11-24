"""
Build every table and figure for the report and slides FROM results/ ONLY.   (Run last.)

    python -m src.make_report_assets
    python -m src.make_report_assets --tag fake

Writes:
    figures/fig1_parameters_by_group.png   2 x 5 small multiples: each subject as a dot, healthy vs stroke
    figures/fig2_effect_forest.png         AUC (or Cliff's delta) with 95 % CI per parameter, FDR-significant marked
    figures/fig3_correlation.png           Spearman heatmap between the 10 parameters (redundancy)
    figures/fig4_reliability.png           split-half ICC per parameter, healthy and stroke
    figures/fig5_composite_roc.png         ROC of the leave-one-out composite score
    report/generated/table1_definitions.md  parameter name, unit, expected direction (from configs/base.yaml)
    report/generated/table2_group_comparison.md
    report/generated/table3_reliability.md
    report/generated/numbers.md             key numbers as "name: value" lines for the report text

Rules: read numbers only from results/*.csv|json and the config; never type a number by hand.
Style: healthy = #2a78d6 (blue), stroke = #eb6834 (orange); every figure has a legend or labels that do
not rely on colour alone; 300 dpi PNG; titles state what is shown; axis labels with units.
"""
from __future__ import annotations

import argparse

from src.utils import load_config, results_dir

HEALTHY_COLOR = "#2a78d6"
STROKE_COLOR = "#eb6834"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/base.yaml")
    ap.add_argument("--tag")
    a = ap.parse_args()
    cfg = load_config(a.config)
    res = results_dir(cfg, a.tag)

    # TODO fig1: read parameters_subject.csv; one panel per primary parameter; jittered dots per group,
    #            median line; panel title = config name + unit; mark q < alpha from group_comparison.csv.
    # TODO fig2: read group_comparison.csv; horizontal forest plot of AUC with CI, sorted by separation;
    #            vertical line at 0.5; filled marker if q < alpha.
    # TODO fig3: read correlation.csv; diverging colour map (blue-grey-red), values printed in cells.
    # TODO fig4: read reliability.csv; grouped bars of ICC for healthy and stroke, lines at 0.5/0.75/0.9.
    # TODO fig5: read composite_scores.csv; ROC curve + AUC [CI] and permutation p in the legend.
    # TODO tables 1-3 + numbers.md into cfg["paths"]["report_generated"].
    # With --tag, write figures to figures/<tag>/ and tables to report/generated/<tag>/ (kept out of git).
    raise NotImplementedError("make_report_assets: see TODOs")


if __name__ == "__main__":
    main()
