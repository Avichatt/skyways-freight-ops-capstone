# ADR-000: Keep SQLite as the system of record for the capstone

Date: 2026-08-04
Status: Accepted

## Context
The kit ships a SQLite database with foreign keys, check constraints and a partial unique index that prevents two active appointments on one slot. The build has two weeks and one developer. The demo runs on a laptop.

## Options considered
| Option | What it means | Pro | Con |
|---|---|---|---|
| A | Keep SQLite | Zero setup, constraints already written, runs anywhere | Single writer; concurrent demos need care |
| B | Move to PostgreSQL | Real concurrency, closer to production | A day lost to setup and migration, no marks for it |
| C | In-memory Python dicts | Fastest to code | Loses the constraints that prove no double booking |

## Decision
We choose A because the uniqueness index is the proof the panel will ask for, and it already exists.

## Consequences
Concurrency is simulated by `04_build/scripts/replay_scenario.py` using short transactions. The enterprise-grade version in the brief names PostgreSQL with row locks as the upgrade path.
