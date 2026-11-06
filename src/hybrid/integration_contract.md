# Integration contract: unloading predictor to agent

The agent calls the unloading-duration predictor as a tool. The predictor never sees the conversation; it receives structured shipment and candidate-slot information only.

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
  "explanation": "28 pallets on a standard dock in the afternoon; the predicted unloading duration is 61 minutes, with a conservative p90 estimate of 78 minutes."
}
```

## Rules both sides keep

| Rule | Who enforces it |
|---|---|
| The agent uses `unload_p90_min`, not the point estimate, to test whether a slot fits | Agent (`find_feasible_slots`) |
| The predictor returns within 300 ms; otherwise, the agent falls back to the shipment's `expected_unload_min` and records the fallback in the trace | Predictor and agent |
| Every successful prediction carries `model_version`; the trace records it | Predictor |
| The predictor estimates unloading duration only; it never chooses, holds, or confirms a slot | Both |
| The database remains the source of truth for slot availability and appointment status | Agent tools and database |

## Scope boundaries

- This contract supports one ML capability: unloading-duration prediction.
- Late-arrival probability prediction is outside the current capstone scope.
- Slot feasibility is determined using database constraints, arrival information, dock compatibility, and the conservative unloading estimate.
- The agent must not claim that a slot is confirmed merely because it was predicted to fit.