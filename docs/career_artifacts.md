# Career Artifacts: Portfolio Presentation & Resume Points

---

## 1. LinkedIn Post Draft (~150 words)

Excited to share my latest capstone project: **Autonomous Freight Dock Scheduling Agent for SkyWays Logistics**.

In regional supply chains, highway delays trigger chaotic warehouse congestion and bay double-bookings. I designed and built an autonomous **Hybrid Simple** scheduling system that combines natural language understanding with strict ACID database integrity.

Key engineering highlights:
* **Zero Double-Bookings:** Engineered atomic SQLite reservations (`BEGIN IMMEDIATE` with partial unique indexes), proven across multi-threaded race conditions where 4 simultaneous requests compete for a single bay.
* **Predictive ML Pipelines:** Developed a Random Forest unloading duration regressor achieving an 8.08 min MAE (**41.9% improvement** over baseline) with a 15-minute p90 operational buffer, paired with an upgraded HistGradientBoosting classifier delivering **81.7% recall** on delayed inbound trucks.
* **Production-Grade Agent:** Built with LangGraph, featuring deterministic multi-turn constraint filtering and an offline heuristic fallback ensuring 100% test reliability under LLM rate limits.

51 automated regression tests passing in 27 seconds. 

Check out the full architecture and code on GitHub: https://github.com/Avichatt/skyways-freight-ops-capstone

#MachineLearning #LangGraph #DataEngineering #Python #AI #Logistics #SystemDesign

---

## 2. Three XYZ-Formula Resume Bullets

> **Format:** Accomplished **[X]**, as measured by **[Y]**, by doing **[Z]**.

### Bullet 1 (Concurrency & Data Infrastructure):
* **Eliminated dock bay double-booking conflicts (0 collisions under multi-threaded load)** across 4 concurrent driver scheduling requests by architecting an ACID-compliant transactional reservation engine in SQLite using `BEGIN IMMEDIATE` transaction locking and partial unique indexes.

### Bullet 2 (Machine Learning & Predictive Operations):
* **Reduced dock turnaround prediction error by 41.9% (8.08 min vs. 13.90 min MAE)** and caught **81.7% of late arrivals** on an uncorrupted chronological test split by building and deploying a Random Forest regressor with calibrated p90 error buffers and a tuned HistGradientBoosting classification pipeline.

### Bullet 3 (Agentic System Architecture & Reliability):
* **Built a production-grade autonomous scheduling agent maintaining a 100% pass rate across 51 regression tests** by designing a deterministic LangGraph state machine with 4-stage commitment lifecycles (`SHOWN` $\to$ `HELD` $\to$ `REQUESTED` $\to$ `CONFIRMED`) and a resilient zero-downtime heuristic extractor fallback for API rate-limiting resilience.
