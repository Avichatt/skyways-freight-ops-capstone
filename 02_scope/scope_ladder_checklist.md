# Scope ladder checklist

Tick the row you are building. Everything above the row you pick is required; everything below is a future-work slide.

## Agentic track
| Level | Must have | Proof in the repo |
|---|---|---|
| Simple | One driver, one shipment, delay understood, feasible options listed, driver picks one, appointment status changes in the database | A recorded conversation and the appointments table before and after |
| Intermediate | Clarification when the message is ambiguous, hold with expiry, two drivers competing for one slot handled without a double booking, escalation when no slot is feasible | `eval_cases.jsonl` passing, `test_no_double_booking.py` passing |
| Enterprise-grade | Persistence of threads across restarts, tracing of every tool call, a human approval step for high-priority overrides, metrics dashboard | Langfuse or equivalent traces, an interrupt node, a metrics page |

## ML track
| Level | Must have | Proof in the repo |
|---|---|---|
| Simple | Cleaned history, one target (unload minutes or late arrival), honest baseline, one trained model beating the baseline on a time-ordered split | Notebook with the metric table |
| Intermediate | Second target, feature importance explained in business words, calibration or error bands, a "what would the planner do with this number" page | Evaluation report filled |
| Enterprise-grade | Prediction service with a schema, drift check between months, retraining script, model card | FastAPI stub completed, model card in `docs/` |

## Hybrid track
| Level | Must have | Proof in the repo |
|---|---|---|
| Simple | Agentic Simple plus one prediction (unload minutes) used when ranking slots | The tool call visible in a trace |
| Intermediate | Agentic Intermediate plus late-arrival probability used to set the hold expiry or to warn the planner | Integration contract honoured, tests on both sides |
| Enterprise-grade | Both enterprise lists, with the model served behind the contract and versioned | Service plus traces plus model card |
