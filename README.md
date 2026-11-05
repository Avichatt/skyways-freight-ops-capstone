# SkyWays Logistics capstone starter kit

This kit is the working folder for the SkyWays dock-coordination capstone. It contains the business data, templates that shape your thinking, code skeletons that stop the usual mistakes, and the presentation scaffolds you will fill at the end. Nothing in here is a finished answer.

## Folder map

| Folder | What is inside | When you use it |
|---|---|---|
| `data/` | SQLite database, schema and seed SQL, data dictionary, ER diagram, dock visit history (ML), labelled driver messages (agent evaluation) | Day 1 onward |
| `00_setup/` | Environment check script and an example `.env` | Day 1 |
| `01_discover/` | Five Whys worksheet, pain-point depth matrix, discovery prompts, research log | Days 1 to 3 |
| `02_scope/` | PRD-lite, ADR template with one filled example, scope ladder checklist | Days 3 to 4 |
| `03_explore/` | Exploration notebook that traces one driver message through the tables | Day 2 |
| `04_build/agentic/` | Conversation state, typed tool contracts, LangGraph skeleton, prompt files, evaluation cases, the no-double-booking test | Days 5 to 9 (Agentic and Hybrid tracks) |
| `04_build/ml/` | Feature specification, baseline notebook, evaluation report template | Days 5 to 9 (ML and Hybrid tracks) |
| `04_build/hybrid/` | Integration contract between the predictor and the agent, prediction service stub | Days 7 to 9 (Hybrid track) |
| `04_build/scripts/` | Scenario replay and database snapshot utilities | Days 8 to 10 |
| `05_present/` | Ten-minute presentation outline, demo script, README, LinkedIn and resume templates, panel questions | Days 10 to 12 |
| `06_check/` | Definition of done per day and the final self-review checklist | Every day |

## Ten-step start

1. Create a virtual environment and run `pip install -r requirements.txt`.
2. Copy `00_setup/.env.example` to `.env` and add your OpenRouter key (Agentic and Hybrid tracks only).
3. Run `python 00_setup/setup_check.py`. Fix anything it reports before moving on.
4. Open `03_explore/explore_skyways.ipynb` and run it top to bottom.
5. Fill `01_discover/five_whys_worksheet.md` for the pain point you choose.
6. Score your pain points in `01_discover/pain_point_depth_matrix.md`.
7. Write `02_scope/prd_lite.md`. Keep it to one page.
8. Pick your track and your scope level, then record both in `02_scope/adr_001_track_and_scope.md`.
9. Build inside `04_build/`, committing to GitHub at the end of every working day.
10. Fill `05_present/` in the last three days and run `06_check/self_review_checklist.md` before you submit.

## Rules the kit enforces

- The database is the system of record. Your agent or model reads and writes through it, never around it.
- A shown slot is not a held slot, and a held slot is not a confirmed slot. The state machine in the brief is binding.
- Every claim in your presentation must point at a file, a test or a number in your repository.
