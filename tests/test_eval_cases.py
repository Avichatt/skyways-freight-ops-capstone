"""Run eval_cases.jsonl and print a pass/fail table.

Run: pytest tests/test_eval_cases.py -v
"""
import json
import os
import pytest

EVAL_FILE = os.path.join(os.path.dirname(__file__), "eval_cases.jsonl")


def _load_cases():
    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


CASES = _load_cases()


@pytest.mark.parametrize("case", CASES, ids=[c["case_id"] for c in CASES])
def test_eval_case(case):
    """Placeholder: fill in your agent invocation and assertion logic."""
    # TODO: replace this stub with actual agent call + assertion
    #
    # Example structure:
    #   response = run_agent(case["driver_id"], case["messages"])
    #   expect   = case["expect"]
    #   if "intent" in expect:
    #       assert response.intent == expect["intent"]
    #   if "tools_called" in expect:
    #       assert set(expect["tools_called"]).issubset(response.tools_called)
    #   if "must_not" in expect:
    #       for banned in expect["must_not"]:
    #           assert banned not in response.raw_text
    #
    pytest.skip(f"Eval case {case['case_id']} not yet wired up")

