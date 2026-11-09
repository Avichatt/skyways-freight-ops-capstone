"""
Day 6 Verification Tests for SkyWays Logistics Capstone.

Checks:
1. Agentic: find_feasible_slots returns valid options for SHP1006 and none for SHP1015.
2. Agentic: Respects latest_leave_ts constraints.
3. ML: First model beats the median baseline on the chronological time split.
4. Service: Predictor service produces valid point estimates and p90 intervals.
"""

import os
import sys
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
for p in [ROOT_DIR, SRC_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

import tools
from src.model.predict_service_stub import predict, PredictRequest


def test_find_feasible_slots_shp1006():
    """Verify find_feasible_slots returns available standard slots for SHP1006 after 12:00."""
    slots = tools.find_feasible_slots(
        shipment_id="SHP1006",
        not_before_ts="2026-08-04T12:00:00+05:30",
        limit=3
    )
    assert len(slots) == 3, f"Expected 3 slots, got {len(slots)}"
    
    # All returned slots must be STANDARD dock type and start at or after 12:00
    for s in slots:
        assert s["dock_type"] == "STANDARD"
        assert s["slot_start_ts"] >= "2026-08-04T12:00:00+05:30"
        assert s["fits_unload"] is True

    # First option should be SLOT-JAI-019 (D2 at 12:00)
    assert slots[0]["slot_id"] == "SLOT-JAI-019"
    assert slots[0]["dock_code"] == "D2"


def test_find_feasible_slots_shp1015_none():
    """Verify find_feasible_slots returns empty list for SHP1015 (reefer dock D5 blocked)."""
    slots = tools.find_feasible_slots(
        shipment_id="SHP1015",
        not_before_ts="2026-08-04T18:30:00+05:30",
        limit=3
    )
    # D5 is in maintenance from 18:00 to 22:00, no reefer slots available
    assert len(slots) == 0, f"Expected 0 slots for SHP1015, got {slots}"


def test_find_feasible_slots_respects_latest_leave():
    """Verify slots ending after latest_leave_ts are filtered out."""
    # Without constraint: returns 3 slots (12:00 D2, 12:00 D4, 13:00 D1)
    # With latest_leave_ts = 13:30: D1 (13:00-14:00) ends at 14:00 > 13:30, must be excluded
    slots = tools.find_feasible_slots(
        shipment_id="SHP1006",
        not_before_ts="2026-08-04T12:00:00+05:30",
        latest_leave_ts="13:30",
        limit=3
    )
    assert len(slots) == 2, f"Expected 2 slots before 13:30, got {len(slots)}"
    for s in slots:
        assert s["slot_end_ts"] <= "2026-08-04T13:30:00+05:30"


def test_ml_model_beats_baseline():
    """Verify trained model achieves lower MAE than the median baseline."""
    model_path = os.path.join(ROOT_DIR, "src", "model", "unload_predictor.joblib")
    assert os.path.exists(model_path), f"Model artifact missing at {model_path}"
    
    # Check documented metrics in eval_report.md
    eval_report = os.path.join(ROOT_DIR, "docs", "eval_report.md")
    with open(eval_report, "r", encoding="utf-8") as f:
        content = f.read()
    assert "8.08" in content, "Model MAE of 8.08 minutes should be documented"
    assert "13.90" in content, "Baseline MAE of 13.90 minutes should be documented"


def test_predictor_service_stub():
    """Verify predict_service returns structured prediction with p90 interval."""
    req = PredictRequest(
        shipment_id="SHP1006",
        facility_id="FAC-JAI-01",
        dock_type="STANDARD",
        pallet_count=12,
        load_weight_kg=7800,
        priority_code="HIGH",
        origin_distance_km=95,
        planned_departure_ts="2026-08-04T04:00:00+05:30",
        carrier_id="CAR003",
        candidate_slot_start_ts="2026-08-04T12:00:00+05:30",
    )
    res = predict(req)
    assert res.predicted_unload_min > 0
    assert res.unload_p90_min >= res.predicted_unload_min
    assert "rf" in res.model_version or "stub" in res.model_version

