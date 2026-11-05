"""Run this once before anything else: python 00_setup/setup_check.py

It checks the Python version, the packages for your track, the database, its views, and the API key.
Every failure prints the fix next to it.
"""
import importlib, os, sqlite3, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "skyways_freight_operations.db")
ok = True

def check(label, passed, fix=""):
    global ok
    print(("PASS  " if passed else "FAIL  ") + label + ("" if passed else "   ->  " + fix))
    ok = ok and passed

check("Python 3.10 or newer", sys.version_info >= (3, 10), "install Python 3.10+ and recreate the virtual environment")

core = ["pandas", "numpy", "dotenv", "pytest"]
ml = ["sklearn", "xgboost"]
agent = ["langchain", "langgraph", "langchain_openai", "pydantic"]
for group, mods, hint in [("core", core, "pip install -r requirements.txt"),
                          ("ML track", ml, "pip install scikit-learn xgboost"),
                          ("Agentic track", agent, "pip install langchain langgraph langchain-openai pydantic")]:
    for m in mods:
        try:
            importlib.import_module(m); check(f"{group}: {m}", True)
        except ImportError:
            check(f"{group}: {m}", False, hint)

check("database file exists", os.path.exists(DB), "unzip the kit again; data/skyways_freight_operations.db is missing")
if os.path.exists(DB):
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    n = con.execute("select count(*) from shipments").fetchone()[0]
    check(f"shipments table readable ({n} rows)", n == 21, "rebuild: python -c \"import sqlite3;sqlite3.connect('data/skyways_freight_operations.db').executescript(open('data/skyways_schema_and_seed.sql').read())\"")
    for v in ["v_latest_eta", "v_slot_availability", "v_inbound_operational_state", "v_current_facility_queue"]:
        try:
            con.execute(f"select * from {v} limit 1").fetchall(); check(f"view {v}", True)
        except sqlite3.Error as e:
            check(f"view {v}", False, str(e))
    idx = con.execute("select name from sqlite_master where type='index' and name='ux_active_appointment_per_slot'").fetchone()
    check("race-condition index ux_active_appointment_per_slot present", idx is not None, "rebuild the database from the seed SQL")

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"))
except Exception:
    pass
key = os.getenv("OPENROUTER_API_KEY", "")
check("OPENROUTER_API_KEY set (Agentic and Hybrid tracks)", key.startswith("sk-or-"), "copy 00_setup/.env.example to .env and paste your key; ML-only track can ignore this line")

print("\nALL CHECKS PASSED" if ok else "\nFix the FAIL lines above, then run again.")
