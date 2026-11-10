"""
Day 8 Verification Tests: Edge Cases (EC03, EC04, EC06, EC10) and Hybrid Integration.

Covers:
- EC03: Late by one hour triggers clarification question with NO scheduling tool calls.
- EC04: Multiple shipments (DRV004) triggers shipment disambiguation before any action.
- EC06: Reefer arrival during maintenance window triggers escalation with operations mention.
- EC10: Out of scope request (detention payment claim) routes to escalation without tool misuse.
- Hybrid Integration: predict_unload_duration contract honours p90 buffer and timeout fallback.
"""

import os
import shutil
import tempfile
import pytest

import src.tools as tools
from src.agent.agent_skeleton import build_graph

DB_SRC = os.path.join(os.path.dirname(__file__), "..", "data", "skyways_freight_operations.db")


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


@pytest.fixture(scope="module")
def agent_graph():
    return build_graph()


def test_ec03_clarification_no_tools(isolated_db, agent_graph):
    """EC03: 'I am late by one hour' asks for clarification without calling operational tools."""
    state = {
        "thread_id": "THR-EC03",
        "driver_id": "DRV003",
        "commitment_status": "NONE",
        "last_message": "I am late by one hour.",
        "tools_called": []
    }
    out = agent_graph.invoke(state)

    assert out.get("commitment_status") == "NONE"
    assert len(out.get("missing_information", [])) > 0
    # Operational scheduling tools (hold, find slots, request, escalate) must NOT be called
    operational_tools = [t for t in out.get("tools_called", []) if t in ("find_feasible_slots", "hold_slot", "request_confirmation", "escalate")]
    assert len(operational_tools) == 0
    assert len(out.get("reply_to_driver", "")) > 0


def test_ec04_disambiguate_shipment(isolated_db, agent_graph):
    """EC04: DRV004 with two active shipments must be asked which shipment."""
    state = {
        "thread_id": "THR-EC04",
        "driver_id": "DRV004",
        "commitment_status": "NONE",
        "last_message": "Late by 40, reaching 12:10.",
        "tools_called": []
    }
    out = agent_graph.invoke(state)

    assert out.get("commitment_status") == "NONE"
    assert "shipment_id" in out.get("missing_information", [])
    assert "shipment" in out.get("clarification_reason", "").lower() or "load" in out.get("clarification_reason", "").lower()


def test_ec06_reefer_escalation(isolated_db, agent_graph):
    """EC06: Reefer arrival at 18:30 when D5 is in maintenance must escalate to operations."""
    state = {
        "thread_id": "THR-EC06",
        "driver_id": "DRV005",
        "commitment_status": "NONE",
        "last_message": "Evening traffic. ETA 6:30. Can the reefer unload tonight?",
        "tools_called": []
    }
    out = agent_graph.invoke(state)

    assert out.get("commitment_status") == "ESCALATED"
    assert "find_feasible_slots" in out.get("tools_called", [])
    assert "escalate" in out.get("tools_called", [])
    reply = out.get("reply_to_driver", "").lower()
    assert "operation" in reply or "team" in reply or "contact" in reply


def test_ec10_out_of_scope_escalate(isolated_db, agent_graph):
    """EC10: Detention charge dispute is OUT_OF_SCOPE and goes directly to escalate."""
    state = {
        "thread_id": "THR-EC10",
        "driver_id": "DRV006",
        "commitment_status": "NONE",
        "last_message": "Can you pay my detention charges for yesterday?",
        "tools_called": []
    }
    out = agent_graph.invoke(state)

    assert out.get("intent") == "OUT_OF_SCOPE"
    assert out.get("commitment_status") == "ESCALATED"
    assert "escalate" in out.get("tools_called", [])
    # Never called booking or search tools
    assert "find_feasible_slots" not in out.get("tools_called", [])
    assert "hold_slot" not in out.get("tools_called", [])


def test_hybrid_integration_contract(isolated_db):
    """Test predictor integration honours p90 buffer, model_version, and fallback."""
    shipment = {
        "shipment_id": "SHP1006",
        "destination_facility_id": "FAC-JAI-01",
        "load_weight_kg": 17000,
        "pallet_count": 28,
        "priority_code": "NORMAL",
        "expected_unload_min": 45,
        "carrier_id": "CAR003",
        "planned_departure_ts": "2026-08-04T06:40:00+05:30"
    }
    candidate = {
        "dock_type": "STANDARD",
        "slot_start_ts": "2026-08-04T12:30:00+05:30"
    }

    pred = tools.predict_unload_duration(shipment, candidate)
    assert pred["unload_p90_min"] >= pred["predicted_unload_min"]
    assert pred["predicted_unload_min"] > 0
    if not pred["prediction_fallback"]:
        assert pred["model_version"] is not None

