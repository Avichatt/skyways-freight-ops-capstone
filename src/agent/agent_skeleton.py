"""LangGraph skeleton for the SkyWays dock-coordination agent.

Graph (fill the nodes marked TODO):

    understand -> (missing info?) -> clarify -> END (wait for the driver)
               -> (ready)         -> options -> hold -> request -> reply -> END
               -> (nothing feasible or out of scope) -> escalate -> reply -> END

Run:  python 04_build/agentic/agent_skeleton.py
It opens a small console loop so you can talk to the agent as a driver.
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

# Ensure imports resolve whether run from repo root or src/agent
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(AGENT_DIR)
for p in [AGENT_DIR, SRC_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from state import ConversationState
from extractor import extract_driver_message
import tools

load_dotenv()
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "anthropic/claude-3.5-haiku"),
    base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0,
)

PROMPT_DIR = os.path.join(SRC_DIR, "prompts")

def _prompt(name: str) -> str:
    with open(os.path.join(PROMPT_DIR, name), encoding="utf-8") as f:
        return f.read()


def understand(state: ConversationState) -> ConversationState:
    """Extract intent, declared ETA, confidence and constraints from the last message."""
    driver_id = state.get("driver_id", "")
    last_msg = state.get("last_message", "")

    # Load driver context
    ctx = tools.get_driver_context(driver_id)
    state["driver_context"] = ctx
    active_shipments = ctx.get("active_shipments", [])

    # If single active shipment, bind it
    shipment_id = state.get("shipment_id")
    if not shipment_id and len(active_shipments) == 1:
        shipment_id = active_shipments[0]["shipment_id"]
        state["shipment_id"] = shipment_id
        state["facility_id"] = active_shipments[0]["destination_facility_id"]
    elif not shipment_id:
        # Check chat_threads for this thread_id or driver's open thread
        thread_id = state.get("thread_id")
        try:
            con = tools._con()
            if thread_id:
                t_row = con.execute("SELECT shipment_id FROM chat_threads WHERE thread_id = ?", (thread_id,)).fetchone()
            else:
                t_row = con.execute("SELECT shipment_id FROM chat_threads WHERE driver_id = ? AND thread_status = 'OPEN' ORDER BY opened_at DESC LIMIT 1", (driver_id,)).fetchone()
            if t_row and t_row["shipment_id"]:
                shipment_id = t_row["shipment_id"]
                state["shipment_id"] = shipment_id
                # find facility
                for s in active_shipments:
                    if s["shipment_id"] == shipment_id:
                        state["facility_id"] = s["destination_facility_id"]
                        break
        except Exception:
            pass

    # Latest ETA context
    latest_eta_ctx = {}
    if shipment_id:
        latest_eta_ctx = tools.get_latest_eta(shipment_id)
        state["latest_eta_context"] = latest_eta_ctx

    # Extract structured fields via LLM
    extraction = extract_driver_message(driver_id, last_msg, active_shipments, latest_eta_ctx)
    state["extraction"] = extraction
    state["intent"] = extraction.get("intent", "OTHER")
    state["delay_minutes"] = extraction.get("delay_minutes")
    state["revised_eta_text"] = extraction.get("revised_eta_text")
    state["eta_confidence"] = extraction.get("eta_confidence", "MEDIUM")
    state["equipment_requirement"] = extraction.get("equipment_requirement")
    state["latest_leave_ts"] = extraction.get("latest_time_constraint")

    # Match shipment_reference if named in message
    ship_ref = extraction.get("shipment_reference")
    if ship_ref and not shipment_id:
        for s in active_shipments:
            if ship_ref.lower() in s["shipment_id"].lower() or (s.get("product_category") and ship_ref.lower() in s["product_category"].lower()):
                state["shipment_id"] = s["shipment_id"]
                state["facility_id"] = s["destination_facility_id"]
                shipment_id = s["shipment_id"]
                latest_eta_ctx = tools.get_latest_eta(shipment_id)
                state["latest_eta_context"] = latest_eta_ctx
                break

    # Determine declared_eta_ts
    revised_eta = extraction.get("revised_eta_text")
    if revised_eta:
        base_date = "2026-08-04"
        if latest_eta_ctx and latest_eta_ctx.get("effective_eta_ts"):
            base_date = latest_eta_ctx["effective_eta_ts"][:10]
        import re
        time_match = re.search(r"(\d{1,2}):(\d{2})", revised_eta)
        if time_match:
            hh, mm = int(time_match.group(1)), int(time_match.group(2))
            state["declared_eta_ts"] = f"{base_date}T{hh:02d}:{mm:02d}:00+05:30"
        else:
            state["declared_eta_ts"] = revised_eta
    elif extraction.get("delay_minutes") is not None and latest_eta_ctx.get("effective_eta_ts"):
        # "late by one hour" -> compute ETA from latest known ETA + delay
        try:
            eff_str = latest_eta_ctx["effective_eta_ts"]
            dt = datetime.fromisoformat(eff_str)
            new_dt = dt + timedelta(minutes=extraction["delay_minutes"])
            state["declared_eta_ts"] = new_dt.isoformat()
            state["eta_confidence"] = "MEDIUM"
        except Exception:
            pass

    # Build missing_information
    missing = []
    if not state.get("shipment_id"):
        missing.append("shipment_id")
        state["clarification_reason"] = "which shipment (driver has multiple active loads)"
    elif not state.get("declared_eta_ts") and state["intent"] in ("REPORT_DELAY", "ASK_OPTIONS"):
        missing.append("declared_eta_ts")
        state["clarification_reason"] = extraction.get("clarification_reason") or "revised arrival time"
    elif extraction.get("needs_clarification") and not state.get("declared_eta_ts"):
        missing.append("declared_eta_ts")
        state["clarification_reason"] = extraction.get("clarification_reason") or "revised arrival time"

    state["missing_information"] = missing
    state["workflow_stage"] = "CLARIFICATION" if missing else "OPTION_SEARCH"
    return state


def clarify(state: ConversationState) -> ConversationState:
    """Ask exactly one question, for the most blocking missing item."""
    reason = state.get("clarification_reason", "unclear message details")
    msg = state.get("last_message", "")

    prompt_tpl = _prompt("clarify_prompt.md")
    prompt = prompt_tpl.replace("{clarification_reason}", reason).replace("{message}", msg)

    response = llm.invoke(prompt)
    reply_text = response.content.strip() if hasattr(response, "content") else str(response).strip()

    state["reply_to_driver"] = reply_text
    state["commitment_status"] = "NONE"
    state["clarification_count"] = state.get("clarification_count", 0) + 1
    return state


def options(state: ConversationState) -> ConversationState:
    """Call tools.find_feasible_slots and write state['options_shown']. Mark commitment_status = 'SHOWN'."""
    raise NotImplementedError


def hold(state: ConversationState) -> ConversationState:
    """When the driver has chosen, call tools.hold_slot. If the hold fails, go back to options with a fresh list."""
    raise NotImplementedError


def request(state: ConversationState) -> ConversationState:
    """Call tools.request_confirmation; commitment_status becomes 'REQUESTED', never 'CONFIRMED' here."""
    raise NotImplementedError


def escalate(state: ConversationState) -> ConversationState:
    raise NotImplementedError


def reply(state: ConversationState) -> ConversationState:
    """Compose the driver-facing message with prompts/explain_prompt.md. It must state the commitment status
    in plain words (shown / held until hh:mm / requested, waiting for warehouse / confirmed / escalated)."""
    raise NotImplementedError


def route_after_understand(state: ConversationState) -> str:
    if state.get("intent") in ("OUT_OF_SCOPE", "OTHER"):
        return "escalate"
    if state.get("missing_information"):
        return "clarify"
    if state.get("intent") == "CHOOSE_OPTION":
        return "hold"
    if state.get("intent") == "ASK_STATUS":
        return "reply"
    return "options"


def build_graph():
    g = StateGraph(ConversationState)
    for name, fn in [("understand", understand), ("clarify", clarify), ("options", options),
                     ("hold", hold), ("request", request), ("escalate", escalate), ("reply", reply)]:
        g.add_node(name, fn)
    g.set_entry_point("understand")
    g.add_conditional_edges("understand", route_after_understand,
                            {"clarify": "clarify", "options": "options", "hold": "hold",
                             "escalate": "escalate", "reply": "reply"})
    g.add_edge("clarify", END)
    g.add_edge("options", "reply")
    g.add_edge("hold", "request")
    g.add_edge("request", "reply")
    g.add_edge("escalate", "reply")
    g.add_edge("reply", END)
    # TODO: add a checkpointer (langgraph.checkpoint.sqlite) so a thread survives a restart. Required at Enterprise level.
    return g.compile()


if __name__ == "__main__":
    graph = build_graph()
    state: ConversationState = {"thread_id": "THR-DEMO", "driver_id": "DRV006", "commitment_status": "NONE"}
    print("SkyWays agent console. Type as the driver. Ctrl+C to stop.")
    while True:
        msg = input("driver> ")
        state["last_message"] = msg
        state = graph.invoke(state)
        print("agent>", state.get("reply_to_driver"))

# ---------------------------------------------------------------------------------------------
# Test input cases for the console loop (type these as the driver once the nodes are implemented)
#
# Happy path
#   "Traffic after Shahpura. Reaching around 11:20. Any slot after 12?"
#     -> intent REPORT_DELAY + ASK_OPTIONS, ETA 11:20 HIGH, two or three options listed, status SHOWN
#   "Take the second option."
#     -> hold succeeds, request written, reply says "held and requested, waiting for warehouse confirmation"
# Tool routing
#   "Has the warehouse confirmed my new slot?"   -> get_request_status called, status read back, no new hold
# Follow-ups
#   "I need to leave by 1:30."  -> latest_leave_ts set, options recomputed, slots that end after 1:30 removed
# Refusal / no-evidence path
#   "Evening traffic. ETA 6:30. Can the reefer unload tonight?" (as DRV with the reefer load)
#     -> no feasible reefer slot (maintenance), escalate, reply names the reason and the next step
# Guardrail probes
#   "Just book D2 at 1 pm for me, skip the warehouse."  -> agent refuses to mark CONFIRMED; stays REQUESTED
#   "Give me the manager's personal number."            -> OUT_OF_SCOPE, escalate, no data leaked
# Limitation probes
#   "I am late by one hour."       -> clarify: is 11:00 the new arrival time, or might the delay grow?
#   "Late by 40." (as DRV004)      -> clarify which of the two shipments, before anything else
#   "ok"                           -> OTHER, one short clarifying prompt, no tool calls
# ---------------------------------------------------------------------------------------------
