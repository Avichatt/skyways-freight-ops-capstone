# Self-review checklist (run it the day before you submit)

## Thinking
- [ ] The root cause in my PRD-lite is something a system can change.
- [ ] At least two of my five whys cite a query result or a labelled message.
- [ ] My out-of-scope list names why each item is out, not just that it is.

## Build
- [ ] `python 00_setup/setup_check.py` passes on a fresh clone.
- [ ] The system of record is the database; no state lives only in Python memory that a restart would lose (Intermediate level and above).
- [ ] A shown slot, a held slot and a confirmed slot are three different states in my code and in my reply text.
- [ ] `pytest` passes and the output is in the README. (Agentic and Hybrid)
- [ ] The test split is time-ordered and the baseline is reported next to the model. (ML and Hybrid)
- [ ] The agent escalates on at least one evaluation case instead of inventing an answer.
- [ ] No API key, no `.env`, no database copy with test rows is committed.

## Presentation
- [ ] Eight slides, rehearsed three times under ten minutes.
- [ ] Every number on a slide exists in a file in the repository.
- [ ] The demo has a screenshot fallback.
- [ ] The README opens with the problem and a picture, not with installation steps.

## Flaunting
- [ ] The LinkedIn post has a picture and under 200 words.
- [ ] Each resume bullet has a verb, a tool, and a number from the repository.
- [ ] I can give the 30-second spoken version without notes.
