# Pain-point depth matrix

Score every pain point you found. The scores decide which one your capstone solves. Use whole numbers from 1 to 5.

| Pain point | Frequency (how often) | Cost when it happens | Evidence in the data | Solvable in two weeks | Depth reached (whys answered with evidence) | Total |
|---|---|---|---|---|---|---|
| | | | | | | |
| | | | | | | |
| | | | | | | |

Scoring guide

| Score | Frequency | Cost | Evidence | Solvable | Depth |
|---|---|---|---|---|---|
| 1 | once a month | minutes of one person's time | none in the tables | needs new data you do not have | one why |
| 3 | weekly | an hour of coordinator time or a missed slot | present in one table | needs one new table or tool | three whys |
| 5 | several times a day | detention charges, a broken customer promise, a lost dock hour | traceable across three or more tables | buildable with the kit as it is | five whys with evidence |

Choose the highest total unless the "solvable" score is 1 or 2. A pain point that scores high everywhere except solvability is a future-work slide, not a capstone.


--------------------------------------------------------------------------------------------------------------

Pain-point depth matrix
Pain point	Frequency	Cost when it happens	Evidence in the data	Solvable in two weeks	Depth reached	Total
Ambiguous and incomplete driver delay messages	5	4	5	5	3	22
Appointment conflicts and unavailable dock slots	5	5	5	5	3	23
Inaccurate unloading-duration estimates	4	4	4	5	3	20

Each score is an initial assessment based on the exploration evidence, not a measured operational KPI.
Why I assigned these scores
1. Ambiguous driver delay messages — 22/25
- Frequency 5: 75 of 148 labelled messages are REPORT_DELAY. This indicates frequent delay-related communication, although it doesn't establish messages per day.
- Cost 4: Unclear messages can cause coordinator effort and appointment disruption.
- Evidence 5: chat_messages, chat_threads, driver_exceptions and eta_updates.
- Solvability 5: The starter kit includes labelled messages, prompts and agent skeletons.
- Depth 3: We have identified the problem and examples, but have not completed Five Whys.
2. Appointment conflicts and unavailable dock slots — 23/25
- Frequency 5: Multiple appointment and delay cases appear in the operational scenario data. The actual daily frequency still needs validation.
- Cost 5: Conflicts can contribute to waiting, congestion and lost dock capacity.
- Evidence 5: appointments, appointment_slots, dock_status_events, docks and v_slot_availability.
- Solvability 5: The database, slot view and agent tool skeletons are already available.
- Depth 3: We have traced examples such as SHP1006 and SHP1015, but have not completed Five Whys.
3. Inaccurate unloading-duration estimates — 20/25
- Frequency 4: The historical dataset contains 6,040 visits.
- Cost 4: Incorrect estimates can cause overruns and poor scheduling.
- Evidence 4: shipments and the historical visit data provide relevant information.
- Solvability 5: Historical data and an ML notebook are included in the starter kit.
- Depth 3: We have examined missing values, duplicates and differences by dock type, but have not completed Five Whys.
Selected pain point
Highest initial score: 23/25
Appointment conflicts and unavailable dock slots is the provisional winner.

It has the highest initial score and is feasible to build with the supplied database and tools.

The proposed capstone can incorporate the other two problems as supporting capabilities:
- Agentic AI understands driver delay messages.
- ML predicts unloading duration.
- Agentic AI checks actual slot availability and manages appointment requests.

