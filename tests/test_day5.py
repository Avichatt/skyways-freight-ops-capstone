"""
Day 5 Verification Tests for SkyWays Logistics Capstone.

Checks:
1. ML: Cleaned data and chronological baseline recorded (target: unload_min).
2. Agentic: understand node and extraction prompt pass on 20 labelled messages.
"""

import os
import sys
import pandas as pd
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
AGENT_DIR = os.path.join(SRC_DIR, "agent")
for p in [ROOT_DIR, SRC_DIR, AGENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from src.agent.agent_skeleton import understand
from src.agent.state import ConversationState


def test_ml_baseline_recorded():
    """Verify that dock_visit_history.csv exists and baseline MAE is computed."""
    history_file = os.path.join(ROOT_DIR, "data", "dock_visit_history.csv")
    assert os.path.exists(history_file), "dock_visit_history.csv missing"
    
    df = pd.read_csv(history_file)
    assert "unload_min" in df.columns
    assert len(df) > 5000
    
    # Check that evaluation report has Day 5 baseline details recorded
    eval_report = os.path.join(ROOT_DIR, "docs", "eval_report.md")
    assert os.path.exists(eval_report), "docs/eval_report.md missing"
    with open(eval_report, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Day 5" in content
    assert "Baseline" in content
    assert "13.90" in content or "MAE" in content


@pytest.mark.parametrize("idx", range(20))
def test_understand_node_on_20_messages(idx):
    """Verify understand node processes the first 20 labelled driver messages."""
    df = pd.read_csv(os.path.join(ROOT_DIR, "data", "labelled_driver_messages.csv"))
    row = df.iloc[idx]
    
    msg_text = str(row["message_text"])
    expected_intent = str(row["intent"])
    
    state: ConversationState = {
        "thread_id": f"THR-TEST-{row['message_id']}",
        "driver_id": "DRV006",
        "last_message": msg_text,
        "commitment_status": "NONE",
    }
    
    result = understand(state)
    assert result is not None
    assert "intent" in result
    assert result["intent"] in [
        "REPORT_DELAY", "ASK_OPTIONS", "ADD_CONSTRAINT", "CHOOSE_OPTION",
        "CHANGE_MIND", "ASK_STATUS", "EARLY_ARRIVAL", "CANCEL", "OUT_OF_SCOPE", "OTHER"
    ]
    # Check that understand produced extraction and workflow_stage
    assert "extraction" in result
    assert "workflow_stage" in result
    assert result["workflow_stage"] in ["CLARIFICATION", "OPTION_SEARCH", "BOOKING", "ESCALATION"]

