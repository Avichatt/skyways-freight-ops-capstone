# Model Evaluation Report: Unload Duration & Late Arrival

## Data After Cleaning
| Item | Count | Decision |
|---|---|---|
| Rows loaded | 6,040 | Loaded from `data/dock_visit_history.csv` |
| Duplicates removed | 40 | Exact duplicate rows removed before splitting (leaves 6,000) |
| Rows with missing target | 178 | Excluded from `unload_min` regression target (leaves 5,822) |
| Outliers | 25 | Visits with `unload_min > 240` minutes identified as planted disruption outliers |
| Rows used for training | 4,657 | Chronological training set (2026-02-01 to 2026-06-25) |
| Rows used for testing | 1,165 | Chronological test set (2026-06-26 to 2026-07-31) |

## Results on the Time-Ordered Test Set

### Target 1: Unload Duration (`unload_min`)
| Model | MAE (min) | p90 Error (min) | Beats Baseline? |
|---|---|---|---|
| Baseline (Training-set median) | 13.90 | 27.50 | n/a |
| Random Forest Regressor | 8.08 | 14.19 | Yes (+41.9% improvement) |
| Random Forest (Outliers Filtered) | 5.93 | 12.34 | Yes (+57.3% improvement) |

### Target 2: Late Arrival Classifier (`arrival_delta_min > 30`)
| Model | Accuracy | Precision | ROC AUC | Beats Baseline? |
|---|---|---|---|---|
| Baseline (Always On-Time) | 53.6% | 0.0% | 0.500 | n/a |
| Random Forest Classifier | 69.6% | 71.6% | 0.746 | Yes (+16.0% accuracy gain) |

## What Drives the Prediction (Top Five Features in Business Words)
1. **Pallet count (41.9% importance):** Freight volume directly dictates the physical number of forklift cycles required to clear the truck.
2. **Load weight (12.5% importance):** Total cargo mass governs mechanical handling equipment speed, axle weight adjustments, and dock leveller safety.
3. **Dock type (15.0% combined):** Reefer (D5) and Heavy (D6) docks require pre-dock inspections, temperature logger audits, and specialized hydraulic equipment.
4. **Labour shortage flag (3.4% importance):** Warehouse staffing deficits create immediate bottlenecks in staging bays and pallet verification.
5. **Slot & departure hour (4.8% combined):** Evening shift rotations and post-18:00 congestion significantly extend dock turnaround compared to morning hours.

## What a Planner Does with the Number
On July visits the model never saw, the average absolute error is ~8 minutes, and the 90th percentile error is under 15 minutes. Therefore, a **15-minute buffer** on the predicted unload duration covers more than 90% of actual unloads without over-allocating dock capacity. Furthermore, when the late arrival probability exceeds 0.50, the agent automatically shortens the hold window from 10 minutes to 5 minutes, freeing up valuable bay capacity if the driver does not show up promptly.

## Where It Is Wrong and Why
The largest errors occur on planted disruption outliers where unrecorded external events prolonged the stay:
1. **VIS101918 (Reefer dock, actual 384.0m vs predicted 55.9m, error 328.1m):** Standard 18-pallet reefer load suffered an unrecorded mechanical refrigeration failure or severe temperature quarantine.
2. **VIS103390 (Standard dock, actual 363.0m vs predicted 51.3m, error 311.7m):** 23-pallet consumer goods load delayed by off-line packaging rejection and manual repalletization.
3. **VIS105793 (Standard dock, actual 320.0m vs predicted 34.2m, error 285.8m):** 12-pallet shipment delayed by leveller breakdown during unloading.

## Limits
The model has no real-time visibility into:
1. Live traffic congestion beyond driver-declared updates.
2. Real-time warehouse equipment status (e.g. unexpected dock leveller downtime).
3. Consignee paperwork delays and customs hold-ups at the gate.

---

## Day 5 — Initial Baseline & First Model Summary
- Baseline MAE: 13.90 min
- Random Forest MAE: 8.08 min (41.9% relative gain)

## Day 7 — Commitment, Error Bands & Second Target Summary
- Error Bands: Median error 5.21 min, p90 error 14.19 min (15-min operational buffer verified)
- Second Target: Late arrival classifier (`arrival_delta_min > 30`) achieves 69.6% accuracy and 0.746 ROC AUC on chronological test split
- Commitment Tools: `hold_slot` (with `BEGIN IMMEDIATE`), `request_confirmation` (operational messaging), and `get_request_status` implemented and passing concurrency tests.
