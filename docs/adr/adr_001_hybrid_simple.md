# ADR-001: Hybrid Simple Architecture & Atomic Database Holds

Date: 2026-08-04
Status: Accepted

## Context
SkyWays experiences two interconnected failure modes:
1. Two coordinators offer the same dock slot to two drivers within two minutes because availability is a manual screen-reading rather than an atomic state.
2. Inbound unloads routinely overrun fixed 60-minute windows because duration is assumed rather than predicted from historical load characteristics (weight, pallets, dock type).

The capstone must solve the concurrency problem while proving that predictive sizing prevents dock overruns, fitting within the 10-day build timeframe.

## Options considered

| Option | What it means | Pro | Con |
|---|---|---|---|
| **A: Pure Agentic AI** | Conversational LangGraph agent over SQLite using fixed 60-minute slot durations. | Simplest architecture; focused entirely on state machine and concurrency. | Leaves the second root cause untouched; unloads continue to overrun and create yard congestion. |
| **B: Pure Machine Learning** | Train models on historical visits to predict unload duration and display predictions on a planner dashboard. | Deep model evaluation on a time-ordered split; directly attacks duration variance. | Does not solve the coordination bottleneck; human coordinators will still double-book slots during disruptions. |
| **C: Hybrid Simple (Chosen)** | LangGraph agent coordinates exceptions and acquires atomic database holds, querying an ML regressor for conservative p90 unload duration. | Attacks both root causes; agent uses data-driven p90 duration to filter out overrun-prone slots while database index guarantees zero double-bookings. | Requires building and testing two components behind a strict integration contract with fallback handling. |

## Decision
We choose **Option C (Hybrid Simple)** because neither an agent without duration intelligence nor an ML model without transactional booking capability solves the freight coordination bottleneck. 

Under this decision:
1. **The LLM decides what to say** (intent extraction, targeted clarification, explanation). It never executes SQL or declares availability.
2. **The typed tools and ML model decide what is true** (`find_feasible_slots` checks physical compatibility and enforces p90 unload fit).
3. **The SQLite database decides what is committed** (`hold_slot` uses `BEGIN IMMEDIATE` and the partial unique index `ux_active_appointment_per_slot` to atomically arbitrate write races).
4. **Hold expiry persistence:** Holds are temporary 10-minute reservations tracked with `hold_expires_at` and released via `release_expired_holds()`.
5. **Fallback:** If the ML predictor fails or exceeds its 300ms SLA, the tool falls back gracefully to `expected_unload_min` from the database.

## Consequences
- **What becomes easier:** The agent never offers a 45-minute slot for a 75-minute unload; coordinators stop receiving duplicate booking complaints.
- **What becomes harder:** The test harness must validate both agentic conversational workflows and statistical ML evaluation metrics on a time split.
- **What to revisit in Enterprise:** Replace SQLite single-writer transactions with PostgreSQL row-level locks, and upgrade single-shipment slot search to facility-wide CP-SAT rolling horizon optimization.
