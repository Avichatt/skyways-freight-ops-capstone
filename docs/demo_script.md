# SkyWays Smart Dock Coordination — 3-Minute Live Demo Script

Six moves in three minutes, each with the words to say and the exact system output the panel must see. Rehearse three times from a clean restored database snapshot.

---

### Setup 

```bash
# Ensure clean state from snapshot
python scripts/snapshot_db.py restore
```

Have two terminal windows open side-by-side:

- **Terminal 1:** Driver interactive console (`python src/agent/agent_skeleton.py`)
- **Terminal 2:** Ready to run the concurrency replay (`python scripts/replay_scenario.py`)

---

### The 3-Minute Choreography

| Time           | Action                                                                              | What You Say                                                                          | What the Panel Sees                                                                                                                                         |
| :------------- | :----------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **0:00** | Driver message:`Traffic after Shahpura. Reaching around 11:20. Any slot after 12?` | *"A real message from the dataset. Watch which tools fire."*                        | Understand extracts ETA 11:20 and 12:00 constraint; `find_feasible_slots` returns 3 numbered options. Status: **SHOWN**.                            |
| **0:40** | Driver message:`I need to leave by 1:30.`                                          | *"A constraint. The list shrinks without me asking anything again."*                | Constraint parsed as `latest_leave_ts = 13:30`. Slot ending at 14:00 drops out. Status: **SHOWN**.                                                  |
| **1:10** | Driver message:`Take the first one.`                                               | *"Held, not confirmed. The warehouse still has to say yes."*                        | Agent executes `hold_slot` then `request_confirmation`. SQLite `appointments` gains a row with `PENDING_CONFIRMATION`. Status: **REQUESTED**. |
| **1:40** | Run in Terminal 2:`python scripts/replay_scenario.py`                              | *"Four trucks want the same slot at once. The database allows exactly one."*        | 4 concurrent threads race for `SLOT-JAI-019`. Output: `1 HELD, 3 REJECTED`. Index prevents double booking.                                              |
| **2:20** | Driver message:`Evening traffic. ETA 6:30. Can the reefer unload tonight?`         | *"No feasible slot. The agent does not invent one; it escalates with a reason."*    | Facility rule check finds reefer door D5 is down under maintenance. Status: **ESCALATED** with explanation.                                           |
| **2:50** | Stop.                                                                                | *"That is the loop: understand, option, hold, request, and refuse when it should."* | Timer stops before 3:00. Transition to Proof slide.                                                                                                         |

---

### Fallback Recovery Plan

> [!WARNING] ⚠️ If External Network Fails During Live Demo
> Switch smoothly to the screenshot fallback in Slide 5:
> *"Here is the recorded trace of what you would have seen in normal network conditions."*
> Keep the exact timing. A presenter who recovers cleanly in 10 seconds scores higher than one who stumbles.
