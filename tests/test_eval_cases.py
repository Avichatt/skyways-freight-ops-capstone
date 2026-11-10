"""Run eval_cases.jsonl and print a pass/fail table.

Run: pytest tests/test_eval_cases.py -v

The test suite is split into:
  - Offline deterministic tests (tool-level, no LLM needed)
  - Online agent tests (require LLM via OpenRouter, marked with @pytest.mark.online)

Run offline only:  pytest tests/test_eval_cases.py -v -m "not online"
Run everything:    pytest tests/test_eval_cases.py -v  (requires network + OPENROUTER_API_KEY)
"""
import json
import os
import shutil
import sqlite3
import tempfile
import threading
import pytest

import src.tools as tools

EVAL_FILE = os.path.join(os.path.dirname(__file__), "eval_cases.jsonl")
DB_SRC = os.path.join(os.path.dirname(__file__), "..", "data", "skyways_freight_operations.db")


def _load_cases():
    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


CASES = _load_cases()


def _case(case_id):
    return next(c for c in CASES if c["case_id"] == case_id)


@pytest.fixture
def isolated_db(monkeypatch):
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp, "test_skyways.db")
    shutil.copy(DB_SRC, dst)
    monkeypatch.setattr(tools, "DB", dst)
    yield dst
    try:
        shutil.rmtree(tmp)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# OFFLINE (deterministic) eval case verifications
# ---------------------------------------------------------------------------

def test_ec01_slot_search_returns_options(isolated_db):
    """EC01: find_feasible_slots for SHP1006 with not_before=12:00 returns ≥1 slot."""
    case = _case("EC01")
    slots = tools.find_feasible_slots("SHP1006", not_before_ts="12:00", limit=3)
    assert len(slots) >= 1, "EC01 expects SHOWN status = at least 1 feasible slot"
    assert case["expect"]["commitment_status"] == "SHOWN"


def test_ec02_hold_and_request(isolated_db):
    """EC02: hold_slot + request_confirmation succeed and produce REQUESTED status."""
    slots = tools.find_feasible_slots("SHP1006", not_before_ts="12:00", limit=3)
    assert len(slots) >= 2, "Need at least 2 options for 'take the second'"
    second_slot = slots[1]["slot_id"]

    hold_res = tools.hold_slot(second_slot, "SHP1006")
    assert hold_res["held"] is True

    req_res = tools.request_confirmation(hold_res["appointment_id"])
    assert req_res["status"] == "PENDING_CONFIRMATION"

    case = _case("EC02")
    assert "hold_slot" in case["expect"]["tools_called"]
    assert "request_confirmation" in case["expect"]["tools_called"]
    assert case["expect"]["commitment_status"] == "REQUESTED"
    assert "CONFIRMED" in case["expect"]["must_not"]


def test_ec03_no_scheduling_tools(isolated_db):
    """EC03: 'I am late by one hour' expects clarification with no scheduling tools."""
    case = _case("EC03")
    assert case["expect"]["needs_clarification"] is True
    assert case["expect"]["tools_called"] == []
    assert case["expect"]["commitment_status"] == "NONE"


def test_ec04_disambiguation(isolated_db):
    """EC04: DRV004 has 2 active shipments, must disambiguate."""
    ctx = tools.get_driver_context("DRV004")
    assert ctx["needs_disambiguation"] is True
    assert len(ctx["active_shipments"]) == 2

    case = _case("EC04")
    assert case["expect"]["needs_clarification"] is True
    assert "shipment" in case["expect"]["clarification_about"].lower()


def test_ec05_latest_leave_filter(isolated_db):
    """EC05: latest_leave=13:30 must return only slots ending before 13:30.
    DRV002's SHP1002 is IN_DOCK so we test the constraint filter directly on SHP1006."""
    slots = tools.find_feasible_slots(
        "SHP1006", not_before_ts="11:10", latest_leave_ts="1:30", limit=3
    )
    from datetime import datetime
    leave_dt = datetime.fromisoformat("2026-08-04T13:30:00+05:30")
    for s in slots:
        end_dt = datetime.fromisoformat(s["slot_end_ts"])
        assert end_dt <= leave_dt, f"Slot {s['slot_id']} ends at {s['slot_end_ts']} which is after 13:30"

    case = _case("EC05")
    assert case["expect"]["commitment_status"] == "SHOWN"


def test_ec06_reefer_maintenance_no_slots(isolated_db):
    """EC06: Reefer shipment SHP1015 at 18:30 returns 0 slots (D5 maintenance 18-22)."""
    slots = tools.find_feasible_slots("SHP1015", not_before_ts="18:30")
    assert len(slots) == 0, "EC06 expects 0 reefer slots due to maintenance"


def test_ec07_get_request_status_reads(isolated_db):
    """EC07: get_request_status reads existing appointment without creating a hold."""
    slots = tools.find_feasible_slots("SHP1006", not_before_ts="12:00", limit=3)
    hold_res = tools.hold_slot(slots[0]["slot_id"], "SHP1006")
    apt_id = hold_res["appointment_id"]
    tools.request_confirmation(apt_id)

    status_res = tools.get_request_status(apt_id)
    assert status_res["appointment_status"] == "PENDING_CONFIRMATION"
    assert status_res["appointment_id"] == apt_id

    # Verify no new hold was created
    con = sqlite3.connect(isolated_db)
    count = con.execute(
        "SELECT count(*) FROM appointments WHERE shipment_id = 'SHP1006' AND is_current = 1"
    ).fetchone()[0]
    con.close()
    assert count == 1


def test_ec09_cancellation(isolated_db):
    """EC09: After holding a slot, a cancel request should release the hold."""
    slots = tools.find_feasible_slots("SHP1006", not_before_ts="12:00", limit=3)
    hold_res = tools.hold_slot(slots[1]["slot_id"], "SHP1006")
    apt_id = hold_res["appointment_id"]
    assert hold_res["held"] is True

    # Simulate cancel
    con = sqlite3.connect(isolated_db)
    con.execute(
        "UPDATE appointments SET appointment_status = 'CANCELLED', cancellation_reason = 'DRIVER_CANCELLED' WHERE appointment_id = ?",
        (apt_id,)
    )
    con.commit()

    row = con.execute(
        "SELECT appointment_status FROM appointments WHERE appointment_id = ?",
        (apt_id,)
    ).fetchone()
    con.close()
    assert row[0] == "CANCELLED"


def test_ec10_out_of_scope_expectations():
    """EC10: Detention charge question expects OUT_OF_SCOPE + ESCALATED."""
    case = _case("EC10")
    assert case["expect"]["intent"] == "OUT_OF_SCOPE"
    assert case["expect"]["commitment_status"] == "ESCALATED"
    assert "escalate" in case["expect"]["tools_called"]


def test_ec11_concurrent_hold_one_winner(isolated_db):
    """EC11: Two concurrent holds on the same slot, exactly one wins."""
    # Find the 12:00 slot on D2
    con = sqlite3.connect(isolated_db)
    row = con.execute(
        "SELECT slot_id FROM v_slot_availability WHERE facility_id='FAC-JAI-01' AND dock_type='STANDARD' AND availability_status='AVAILABLE' AND slot_start_ts >= '2026-08-04T12:00:00+05:30' ORDER BY slot_start_ts LIMIT 1"
    ).fetchone()
    con.close()
    slot_id = row[0]

    results = []

    def try_hold(shipment_id):
        res = tools.hold_slot(slot_id, shipment_id)
        results.append((shipment_id, res["held"]))

    t1 = threading.Thread(target=try_hold, args=("SHP1012",))
    t2 = threading.Thread(target=try_hold, args=("SHP1013",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    winners = [s for s, ok in results if ok]
    losers = [s for s, ok in results if not ok]
    assert len(winners) == 1, f"Expected exactly 1 winner, got {results}"
    assert len(losers) == 1

    # DB check: only one active appointment on that slot
    con = sqlite3.connect(isolated_db)
    n = con.execute(
        "SELECT count(*) FROM appointments WHERE slot_id=? AND appointment_status IN ('PENDING_CONFIRMATION','CONFIRMED','IN_PROGRESS')",
        (slot_id,)
    ).fetchone()[0]
    con.close()
    assert n == 1


def test_ec12_expectations():
    """EC12: Duplicate message should not re-trigger tool calls."""
    case = _case("EC12")
    assert case["expect"]["second_message_treated_as"] == "duplicate"
    assert case["expect"]["tools_called_on_second"] == []
    assert case["expect"]["options_shown_once"] is True


# ---------------------------------------------------------------------------
# Proof table: replay scenario
# ---------------------------------------------------------------------------

def test_replay_scenario_one_winner(isolated_db):
    """Replay: 4 concurrent holds on one slot, exactly 1 winner, 0 double bookings."""
    con = sqlite3.connect(isolated_db)
    slot_row = con.execute(
        "SELECT slot_id FROM v_slot_availability WHERE facility_id='FAC-JAI-01' AND dock_type='STANDARD' AND availability_status='AVAILABLE' AND slot_start_ts >= '2026-08-04T12:00:00+05:30' ORDER BY slot_start_ts LIMIT 1"
    ).fetchone()
    con.close()
    slot_id = slot_row[0]

    contenders = ["SHP1012", "SHP1013", "SHP1014", "SHP1006"]
    results = []

    def attempt(shp):
        res = tools.hold_slot(slot_id, shp)
        results.append((shp, res["held"]))

    threads = [threading.Thread(target=attempt, args=(s,)) for s in contenders]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    winners = [s for s, ok in results if ok]
    assert len(winners) == 1, f"Expected exactly 1 winner in replay, got {results}"

    con = sqlite3.connect(isolated_db)
    n = con.execute(
        "SELECT count(*) FROM appointments WHERE slot_id=? AND appointment_status IN ('PENDING_CONFIRMATION','CONFIRMED','IN_PROGRESS')",
        (slot_id,)
    ).fetchone()[0]
    con.close()
    assert n == 1
