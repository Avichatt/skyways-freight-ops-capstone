# Panel Defense Preparation: 10 Standard Questions & Model Answers

This document provides structured, evidence-backed answers for the 10 core technical questions during the capstone panel defense.

---

### Q1: Why did you choose a Hybrid architecture over a pure LLM agent or traditional rule engine?
**Model Answer:**
A pure LLM architecture lacks deterministic consistency and cannot guarantee ACID transactions; in testing, LLMs hallucinate non-existent slots and suffer multi-second API latencies. Conversely, a pure heuristic rule engine lacks natural language flexibility and breaks on conversational driver constraints like *"I need to leave before 1:30 PM"*. 

Our **Hybrid Simple** pattern achieves the best of both worlds:
1. **LLM & Extractor:** Handles conversational language extraction and intent recognition.
2. **LangGraph State Machine:** Governs workflow states deterministically.
3. **Dedicated ML Regressors/Classifiers:** Provide millisecond-level duration and risk inference.
4. **SQLite Database with ACID Locks:** Serves as the single system of record. The LLM never touches SQL directly.

---

### Q2: How do you prevent the LLM from hallucinating SQL queries or booking unauthorized slots?
**Model Answer:**
The LLM is completely isolated from the database. It is never given raw SQL execution capabilities or direct write access. 
* All database interactions occur strictly through typed, compiled Python tools ([`src/tools.py`](file:///c:/Users/Avi/Downloads/skyways_capstone_starter_kit/skyways_capstone_starter/src/tools.py)).
* The LLM only parses driver constraints (e.g. ETA, leave time).
* The tool [`find_feasible_slots`](file:///c:/Users/Avi/Downloads/skyways_capstone_starter_kit/skyways_capstone_starter/src/tools.py) runs 6 hard mathematical checks (dock equipment compatibility, operational operating hours, weight limits, active overlap collision checks, and duration fit).
* A slot can only be reserved if it passes database constraints; hallucinated slot IDs are rejected immediately.

---

### Q3: What happens if the Unload Duration ML model under-predicts or over-predicts?
**Model Answer:**
In logistics, asymmetric risk matters: under-predicting an unload duration causes physical dock bay congestion, whereas over-predicting wastes slot capacity.
* To protect against under-prediction, we calibrated a **14.19-minute p90 error buffer** on top of the model's 8.08-minute MAE prediction.
* Our error band analysis demonstrates that `predicted_unload + 15 min buffer` covers $\ge 90\%$ of actual unloading visits on July test data.
* If the prediction service stub is unavailable or times out (>300ms SLA), the system seamlessly falls back to historical database defaults (45m for standard, 60m for reefer).

---

### Q4: How does your system prevent double-booking when multiple drivers request the same slot simultaneously?
**Model Answer:**
We eliminate double-booking at the database layer through two interlocking mechanisms:
1. **SQLite `BEGIN IMMEDIATE` Locking:** When [`hold_slot()`](file:///c:/Users/Avi/Downloads/skyways_capstone_starter_kit/skyways_capstone_starter/src/tools.py) is called, it acquires a reserved transaction lock before querying slot availability, ensuring no interleaved reads between concurrent threads.
2. **Partial Unique Constraint:** The `appointments` table enforces a database-level unique index:
   ```sql
   CREATE UNIQUE INDEX ux_active_appointment_per_slot 
   ON appointments(slot_id) 
   WHERE appointment_status IN ('PENDING_CONFIRMATION', 'CONFIRMED', 'IN_PROGRESS');
   ```
If four drivers simultaneously attempt to hold the exact same slot, the first thread commits successfully and the remaining three immediately raise an `IntegrityError`, returning `held=False, reason="slot taken"`. This is verified deterministically in `tests/test_no_double_booking.py` and `scripts/replay_scenario.py`.

---

### Q5: Why is the commitment state separated into SHOWN, HELD, REQUESTED, and CONFIRMED?
**Model Answer:**
In enterprise logistics, confusing information presentation with contractual commitment leads to costly driver claims and warehouse penalties:
* **`SHOWN`:** Feasible options displayed to the driver. Zero capacity is committed; other drivers can still view and take these slots.
* **`HELD`:** An atomic, temporary 10-minute hold placed on the slot (`PENDING_CONFIRMATION`), locking out other drivers.
* **`REQUESTED`:** An asynchronous operational dispatch (`operational_messages`) is sent to the warehouse coordinator.
* **`CONFIRMED`:** A human warehouse coordinator explicitly approves the booking. 

The autonomous agent is strictly forbidden from declaring `CONFIRMED`. Only the warehouse human coordinator can confirm an appointment.

---

### Q6: How do you handle non-English, noisy, or Hinglish driver messages?
**Model Answer:**
Indian freight corridors frequently involve Hinglish phrasing (e.g., *"Bhai accident ahead on highway ho gaya Pataudi road ke paas, 60 min late hounga"*).
* Our extractor combines few-shot prompting on LLMs with a regex-driven conversational fallback.
* The extractor searches specifically for time markers, numeric delays, and corridor landmarks (e.g. Shahpura, Kotputli, Kishangarh) rather than requiring grammatical syntax.
* If the message is completely ambiguous (e.g., *"Late hounga thoda"*), the agent invokes the `CLARIFICATION` node without calling scheduling tools, asking for a definitive ETA.

---

### Q7: How does the system handle OpenRouter / LLM rate limits or network outages?
**Model Answer:**
We designed a **zero-downtime heuristic fallback extractor** in [`src/agent/extractor.py`](file:///c:/Users/Avi/Downloads/skyways_capstone_starter_kit/skyways_capstone_starter/src/agent/extractor.py):
* If the external LLM API returns HTTP 429 (Rate Limit Exceeded), 503, or drops network connectivity, the system catches the exception and routes the raw text through a local deterministic regex parser.
* The heuristic extractor identifies delay declarations, ETAs, departure constraints, and numeric option choices (`first one` $\to$ `"1"`).
* This ensures that all 51 automated regression tests and core scheduling workflows run 100% offline without external network dependency.

---

### Q8: Why did you choose HistGradientBoosting instead of Random Forest or Deep Learning for late arrival risk?
**Model Answer:**
On the chronological July test set:
1. **Random Forest:** Achieved 69.6% accuracy and 0.745 ROC AUC.
2. **HistGradientBoosting:** Boosted accuracy to **70.07%**, ROC AUC to **0.7512**, and improved probability calibration (Brier score of 0.2009).
3. **Inference Latency & Size:** HistGradientBoosting bins continuous features into 256 integer histograms, reducing artifact size from 35 MB (Random Forest) to **650 KB**, with sub-millisecond prediction latency.
4. **Threshold Tuning:** By lowering the decision threshold to $\theta = 0.30$, we achieve **81.7% Recall**, successfully catching more than 4 out of 5 delayed trucks before arrival.

---

### Q9: How would you scale this system to 100+ facilities in production?
**Model Answer:**
While SQLite is optimal for local development and embedded edge testing:
1. **Database Migration:** Replace SQLite with **PostgreSQL on Cloud SQL**, using row-level locking (`SELECT FOR UPDATE`) and advisory locks per facility.
2. **Microservice Containerization:** Package the FastAPI predictor stub and LangGraph agent into **Docker** containers deployed on **Google Cloud Run** or **GKE** (Google Kubernetes Engine) with horizontal pod autoscaling.
3. **Partitioning:** Partition tables by `facility_id` so that high-volume regional hubs (e.g. JAI-01, GGN-01) scale compute and IOPS independently without cross-facility lock contention.
4. **Caching & Asynchronous Messaging:** Utilize Redis for caching slot availability views and Google Cloud Pub/Sub for resilient driver WhatsApp/SMS notification dispatch.

---

### Q10: What are the three primary operational limits of your current system?
**Model Answer:**
As documented in our PRD-lite and architecture review:
1. **Single-Facility Horizon:** The agent manages individual arrivals at their destination hub; it does not solve multi-stop combinatorial vehicle routing across multiple transshipment points.
2. **Human-in-the-Loop Dependency:** The system automates option discovery and temporary holds, but requires a human warehouse coordinator to officially confirm the appointment (`CONFIRMED`).
3. **Static Expiry Window:** Holds expire after a fixed 10-minute window rather than dynamically scaling based on driver proximity or telemetry traffic congestion.

