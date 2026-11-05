# <Project name>: dock coordination for SkyWays Logistics

One line on what it does and for whom.

![architecture](docs/architecture.png)

## The problem
Two or three sentences with the number that proves it matters. Link to `docs/five_whys.md`.

## What it does
- Bullet one, in the user's words.
- Bullet two.
- Bullet three.

## Demo
A 60-second GIF or a link to a video. Then the three commands that reproduce it:
```
pip install -r requirements.txt
python 00_setup/setup_check.py
python app.py
```

## Architecture
The C4 container diagram and one paragraph per container. Link the ADRs in `docs/adr/`.

## Proof
| Claim | Evidence |
|---|---|
| No double booking under concurrent requests | `pytest tests/test_no_double_booking.py` output |
| Model beats the baseline on a time-ordered split | `docs/eval_report.md` |

## Limits and next steps
Three honest limits, two next steps.

## Data
Classroom dataset, synthetic, snapshot date 4 August 2026. Schema in `data/skyways_data_dictionary.csv`.
