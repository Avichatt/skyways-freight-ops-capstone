# Demo script (three minutes)

Before you start: `python 04_build/scripts/snapshot_db.py restore`, open the database viewer on the `appointments` table, open the agent console or UI, open the terminal for the replay script.

| Step | You type or click | You say while it runs | What the panel sees |
|---|---|---|---|
| 1 (0:00) | Driver message: "Traffic after Shahpura. Reaching around 11:20. Any slot after 12?" | "A real message from the dataset. Watch which tools fire." | Options listed, status SHOWN |
| 2 (0:40) | "I need to leave by 1:30." | "A constraint. The list shrinks without me re-asking anything." | One option drops out |
| 3 (1:10) | "Take the first one." | "Held, not confirmed. The warehouse still has to say yes." | appointments table gains a PENDING_CONFIRMATION row |
| 4 (1:40) | Run `replay_scenario.py` | "Four trucks want the same slot at once. The database allows exactly one." | Terminal prints one HELD, three REJECTED |
| 5 (2:20) | Driver message: "Evening traffic. ETA 6:30. Can the reefer unload tonight?" | "No feasible slot. The agent does not invent one; it escalates with a reason." | Status ESCALATED |
| 6 (2:50) | Stop | "That is the whole loop: understand, option, hold, request, and refuse when it should." | |

ML track variant: replace steps 1 to 3 with the evaluation table, one prediction explained with its drivers, and the planner action it changes. Keep step 4 if your model feeds slot sizing.

If anything fails: switch to the screenshots in slide 5 and keep the timing.
