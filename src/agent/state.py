from typing import TypedDict, Optional, Literal, Any, Union

Intent = Literal[
    "REPORT_DELAY",
    "ASK_OPTIONS",
    "ADD_CONSTRAINT",
    "CHOOSE_OPTION",
    "CHANGE_MIND",
    "ASK_STATUS",
    "EARLY_ARRIVAL",
    "CANCEL",
    "OUT_OF_SCOPE",
    "OTHER",
]

ExtractionResult = dict[str, Any]
SlotOption = dict[str, Any]

class ConversationState(TypedDict, total=False):

    # Identity
    thread_id: str
    driver_id: str
    shipment_id: Optional[str]
    facility_id: Optional[str]

    # Context
    driver_context: dict
    latest_eta_context: dict

    # Driver message
    last_message: str
    extraction: ExtractionResult

    intent: Intent
    delay_minutes: Optional[int]
    declared_eta_ts: Optional[str]
    revised_eta_text: Optional[str]
    eta_confidence: Literal["HIGH", "MEDIUM", "LOW"]

    equipment_requirement: Optional[
        Literal["STANDARD", "REEFER", "HEAVY"]
    ]
    latest_leave_ts: Optional[str]

    missing_information: list[str]
    clarification_reason: str
    clarification_count: int

    # Scheduling
    options_shown: list[SlotOption]
    held_slot_id: Optional[str]
    hold_expires_at: Optional[str]

    appointment_id: Optional[str]

    commitment_status: Literal[
        "NONE",
        "SHOWN",
        "HELD",
        "REQUESTED",
        "CONFIRMED",
        "ESCALATED"
    ]

    workflow_stage: Literal[
        "EXTRACTION",
        "CLARIFICATION",
        "OPTION_SEARCH",
        "BOOKING",
        "CONFIRMATION",
        "ESCALATION"
    ]

    # Output
    reply_to_driver: str
    escalation_reason: Optional[str]
    tools_called: list[str]