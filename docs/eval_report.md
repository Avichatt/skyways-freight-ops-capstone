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
