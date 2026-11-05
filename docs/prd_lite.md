# PRD-lite: <project name>

One page. If it spills to two, the scope is too big for two weeks.

## Problem
<One sentence from the Five Whys root cause. Include the number that proves it matters.>

## Who it is for
| User | What they do today | What changes for them |
|---|---|---|
| Driver | | |
| Operations coordinator | | |
| Warehouse planner | | |

## The one job
<The single outcome the system produces. Example: "turn a free-text delay message into a confirmed, feasible dock slot without a double booking".>

## In scope (this build)
1.
2.
3.

## Out of scope (and why)
1.
2.

## Success measures
| Measure | Baseline today | Target for the demo | How I measure it |
|---|---|---|---|
| | | | |
| | | | |
| | | | |

## Guardrails
What the system never decides on its own:
-
-

## Risks
| Risk | Chance | Impact | What I do about it |
|---|---|---|---|
| | | | |

## Scope level chosen
Simple / Intermediate / Enterprise-grade (circle one) and the one sentence that justifies it.


--------------------------------------------------------------------------------------------------------------


# PRD-lite: SkyWays Smart Dock Coordination

## Problem

On 4 August, shipment SHP1006 had a revised ETA of 11:20 while its existing appointment ended at 11:00; the slot availability view also showed 14 occupied and 7 blocked slots, demonstrating why coordinators need reliable, database-backed appointment feasibility checks.

## Who it is for

| User | What they do today | What changes for them |
|---|---|---|
| Driver | Sends delay updates and communicates a revised arrival time through messages or calls. | Sends a message and receives clarification questions, feasible slot options, and an accurate appointment status. |
| Operations coordinator | Checks shipment details, ETA, appointment records, and dock availability manually. | Uses an agent that retrieves operational context, checks feasible slots, and manages the hold/request workflow. |
| Warehouse planner | Manages dock capacity and handles appointment conflicts. | Receives structured confirmation requests and can see which slots are available, held, or awaiting confirmation. |

## The one job

Turn a driver's delay message into a feasible, database-validated dock-slot option, safely hold the selected slot, request warehouse confirmation, and report the actual status without double-booking.

## In scope (this build)

1. Understand driver delay messages, extract shipment and ETA information, and ask clarification questions when required.
2. Predict unloading duration using one ML model, then use its conservative p90 estimate when checking whether a candidate slot can accommodate the truck.
3. Find feasible slots using operational database records, safely hold the selected slot, request warehouse confirmation, and report the correct commitment status.

## Out of scope (and why)

1. Facility-wide automatic rescheduling, because optimizing every truck and dock requires a larger scheduling system than this two-week capstone.
2. A separate late-arrival prediction model, because the selected Hybrid Simple scope uses only one unloading-duration prediction model.
3. Automatic priority overrides or safety decisions, because these must remain warehouse or human decisions.
4. Automatically declaring an appointment confirmed, because confirmation must come from the warehouse or an authoritative database/tool result.

## Success measures

| Measure | Baseline today | Target for the demo | How I measure it |
|---|---|---|---|
| Double booking | Existing behaviour not yet measured under concurrent requests. | Zero double bookings in the concurrency test. | Run `test_no_double_booking.py` and the scenario replay. |
| Slot feasibility | Manual process; no measured accuracy baseline. | SHP1006 returns valid feasible options; SHP1015 returns no incompatible reefer option when none is available. | Check results against the operational database and evaluation cases. |
| Unloading-duration prediction | Median-by-dock-type baseline not yet measured. | ML model achieves lower MAE than the baseline on the July test data. | Compare MAE using the chronological train/test split. |

## Guardrails

What the system never decides on its own:

- Never invents a slot or treats an `OPEN` slot as automatically `AVAILABLE`.
- Never says `CONFIRMED` unless the authoritative confirmation result says so.
- Never treats a displayed option, a held slot, or a confirmation request as a confirmed appointment.
- Never bypasses dock compatibility, maintenance blocks, or database availability checks.
- Never makes independent priority, safety, or financial decisions.
- Never allows the language model to commit a slot directly; database tools control operational changes.

## Risks

| Risk | Chance | Impact | What I do about it |
|---|---|---|---|
| Driver message is ambiguous or identifies multiple shipments. | High | High | Ask a targeted clarification question before taking action. |
| Two requests attempt to hold the same slot. | Medium | High | Use a SQLite transaction and a database uniqueness constraint; test concurrent requests. |
| Hold expiry is not supported by the existing schema. | Medium | Medium | Inspect the schema before implementation and add only the minimum required support. |
| ML prediction is inaccurate for unusual loads. | Medium | High | Compare against the baseline, use p90 for conservative slot-fit checks, and retain a fallback estimate. |
| Warehouse does not confirm a requested appointment. | Medium | High | Keep the status as `REQUESTED` until an authoritative confirmation is received. |

## Scope level chosen

**Hybrid Simple.**

The project combines a tool-calling agent over SQLite with one unloading-duration prediction model. This keeps the system small enough to complete while demonstrating both intelligent message handling and data-driven slot feasibility.