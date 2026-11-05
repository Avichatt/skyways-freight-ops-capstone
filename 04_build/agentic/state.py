"""Conversation state for the SkyWays dock-coordination agent.

The state is the only thing that moves between graph nodes. Keep it small and typed.
Fields marked TODO are yours to fill once you know what your clarification and hold logic need.
"""
from typing import Literal, Optional, TypedDict


class SlotOption(TypedDict):
    slot_id: str
    dock_code: str
    slot_start_ts: str
    slot_end_ts: str
    fits_unload: bool          # unload duration fits inside the window
    reason_shown: str          # one sentence the driver sees


class ConversationState(TypedDict, total=False):
    # Identity and context
    thread_id: str
    driver_id: str
    shipment_id: Optional[str]           # None until disambiguated
    facility_id: Optional[str]

    # What the driver said and what we understood
    last_message: str
    intent: Literal["REPORT_DELAY", "ASK_OPTIONS", "ADD_CONSTRAINT", "CHOOSE_OPTION",
                    "CHANGE_MIND", "ASK_STATUS", "EARLY_ARRIVAL", "CANCEL", "OUT_OF_SCOPE", "OTHER"]
    declared_eta_ts: Optional[str]
    eta_confidence: Literal["HIGH", "MEDIUM", "LOW"]
    latest_leave_ts: Optional[str]       # driver's own constraint, if any
    missing_information: list[str]       # what must be clarified before options can be shown

    # Options and commitment
    options_shown: list[SlotOption]
    held_slot_id: Optional[str]
    hold_expires_at: Optional[str]
    appointment_id: Optional[str]
    commitment_status: Literal["NONE", "SHOWN", "HELD", "REQUESTED", "CONFIRMED", "ESCALATED"]

    # Output
    reply_to_driver: str
    escalation_reason: Optional[str]

    # TODO: add anything your clarification loop needs, for example a turn counter so the agent
    # stops asking after two unanswered clarifications and escalates instead.
