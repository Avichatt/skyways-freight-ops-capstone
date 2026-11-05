# Integration contract: predictor to agent

The agent calls the predictor as a tool. The predictor never sees the conversation; it sees structured facts only.

## Request (agent to predictor)
```json
{
  "shipment_id": "SHP1006",
  "facility_id": "FAC-JAI-01",
  "dock_type": "STANDARD",
  "pallet_count": 28,
  "load_weight_kg": 17000,
  "priority_code": "NORMAL",
  "origin_distance_km": 95,
  "planned_departure_ts": "2026-08-04T06:40:00+05:30",
  "carrier_id": "CAR003",
  "candidate_slot_start_ts": "2026-08-04T12:30:00+05:30"
}
```

## Response (predictor to agent)
```json
{
  "model_version": "unload-xgb-2026-08-04",
  "predicted_unload_min": 61,
  "unload_p90_min": 78,
  "late_arrival_probability": 0.34,
  "explanation": "28 pallets on a standard dock in the afternoon; carrier CAR003 runs late on 4 of 10 trips"
}
```

## Rules both sides keep
| Rule | Who enforces it |
|---|---|
| The agent uses `unload_p90_min`, not the point estimate, to test whether a slot fits | Agent (`find_feasible_slots`) |
| A `late_arrival_probability` above 0.5 shortens the hold to five minutes and adds a warning line to the reply | Agent (`hold`) |
| The predictor returns within 300 ms or the agent falls back to `expected_unload_min` from the shipment and says so in the trace | Predictor and agent |
| Every response carries `model_version`; the trace records it | Predictor |
| The predictor is never asked to choose a slot | Both |
