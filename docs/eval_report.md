# Model evaluation report: <target>

## Data after cleaning
| Item | Count | Decision |
|---|---|---|
| Rows loaded | | |
| Duplicates removed | | |
| Rows with missing target | | |
| Outliers | | kept / capped / removed, because |
| Rows used for training (before <date>) | | |
| Rows used for testing (from <date>) | | |

## Results on the time-ordered test set
| Model | Metric 1 (name) | Metric 2 (name) | Beats baseline? |
|---|---|---|---|
| Baseline (describe it) | | | n/a |
| Model A | | | |
| Model B | | | |

## What drives the prediction (top five features in business words)
1.
2.
3.
4.
5.

## What a planner does with the number
One paragraph. Example shape: "For a 32-pallet reefer load arriving at 19:00 the model predicts 68 minutes with a 90 percent band of 55 to 85, so the planner books a 90-minute window on D5 instead of the default 60."

## Where it is wrong and why
Two or three failure cases from the test set, with the row, the prediction, the truth and your explanation.

## Limits
What the model does not know (weather, driver, equipment) and what would be needed to add it.


## Day 5 — Unloading Duration Baseline

- Dataset: `data/dock_visit_history.csv`
- Target: `unload_min`
- Rows with known target: 5,822
- Split: chronological 80/20
- Training rows: 4,657
- Test rows: 1,165
- Baseline: training-set median
- Training median: 43.00 minutes
- Test MAE: 13.90 minutes
- Test period: 2026-06-26 to 2026-07-31

The baseline predicts the training-set median unloading duration
for every test observation. A more advanced model must beat the
13.90-minute MAE on the same chronological test set.

## Day 5 — Random Forest Unloading-Duration Model

- Dataset: `data/dock_visit_history.csv`
- Target: `unload_min`
- Training rows: 4,657
- Test rows: 1,165
- Split: chronological 80/20
- Model: RandomForestRegressor
- Number of trees: 300
- Minimum samples per leaf: 3
- Random state: 42
- Baseline MAE: 13.90 minutes
- Random Forest MAE: 8.08 minutes
- Absolute improvement: 5.82 minutes
- Relative improvement: 41.9%
- Test period: 2026-06-26 to 2026-07-31

The Random Forest model outperformed the median baseline on the
same chronological test set.

This is an initial evaluation result. Further validation is needed
before production use, including checking feature availability at
prediction time and evaluating the model's prediction errors.
