# Feature specification: dock visit history

Source: `data/dock_visit_history.csv` (6,040 rows, Feb to Jul 2026, two facilities). The file is deliberately imperfect. Clean it before you trust it.

## Targets you may choose
| Target | Column | Type | Rows usable | Business use |
|---|---|---|---|---|
| Unload duration | `unload_min` | regression (minutes) | visits that were not NO_SHOW | Size the slot; a 45-minute slot for a 70-minute unload is a guaranteed overrun |
| Late arrival | `arrival_delta_min > 30` | classification | visits that were not NO_SHOW | Warn the planner early; set hold expiry |
| No-show | `visit_outcome == 'NO_SHOW'` | classification (rare, about 4%) | all visits | Release slots sooner for likely no-shows |

## Candidate features
| Feature | Column(s) | Known at prediction time? | Note |
|---|---|---|---|
| Pallet count | `pallet_count` | Yes (from the shipment) | 2% missing; impute from weight, and say so |
| Dock type | `dock_type` | Yes | REEFER and HEAVY unload slower |
| Weight | `load_weight_kg` | Yes | Collinear with pallets; keep one or explain why both |
| Priority | `priority_code` | Yes | Weak for duration, useful for no-show |
| Origin distance | `origin_distance_km` | Yes | Strong for delay |
| Departure hour | from `planned_departure_ts` | Yes | Later departures hit more traffic |
| Rain | `rain_flag` | Only if you assume a forecast | State the assumption |
| Carrier | `carrier_id` | Yes | One carrier is systematically later; find it |
| Labour shortage | `labour_shortage_flag` | Known on the day | Large effect on unload |
| Arrival hour | from `actual_gate_in_ts` | NO for arrival prediction, YES for unload prediction | Leakage trap: do not use actual arrival to predict lateness |
| Yard wait | `yard_wait_min` | NO | It happens after arrival; leakage for both targets |

## Non-negotiables
- Split by time (`TimeSeriesSplit` or a fixed cut at 1 July 2026). A shuffled split flatters the model and the panel will ask.
- Report a baseline first: the median unload per dock type, or "always on time". Your model must beat it.
- Remove exact duplicate rows (there are 40) and decide what to do with 25 unload outliers above 240 minutes.
- Write the error in minutes a planner can feel: "the median absolute error is 7 minutes, so a 15-minute buffer covers most visits".
