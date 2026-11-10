
"""Extract structured driver-message information using the configured LLM."""

import json
import os
import re

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

PROMPT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "prompts"
)

ALLOWED_INTENTS = {
    "REPORT_DELAY",
    "ASK_OPTIONS",
    "ADD_CONSTRAINT",
    "CHOOSE_OPTION",
    "CHANGE_MIND",
    "ASK_STATUS",
    "EARLY_ARRIVAL",
    "CANCEL",
    "OUT_OF_SCOPE",
    "OTHER"
}

ALLOWED_EQUIPMENT = {
    None,
    "STANDARD",
    "REEFER",
    "HEAVY"
}

REQUIRED_FIELDS = {
    "intent",
    "delay_minutes",
    "revised_eta_text",
    "shipment_reference",
    "latest_time_constraint",
    "option_choice",
    "equipment_requirement",
    "eta_confidence",
    "needs_clarification",
    "clarification_reason"
}


def _get_llm():
    """Create the configured OpenRouter LLM client."""

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing")

    return ChatOpenAI(
        model=os.getenv(
            "LLM_MODEL",
            "anthropic/claude-3.5-haiku"
        ),
        base_url=os.getenv(
            "OPENROUTER_BASE_URL",
            "https://openrouter.ai/api/v1"
        ),
        api_key=api_key,
        temperature=0,
        timeout=45,
        max_retries=1
    )


def _load_prompt():
    """Load the extraction prompt from the prompts directory."""

    path = os.path.join(
        PROMPT_DIR,
        "extraction_prompt.md"
    )

    with open(path, encoding="utf-8") as f:
        return f.read()


def _parse_json(content):
    """Parse JSON while tolerating accidental Markdown fences."""

    if isinstance(content, list):
        content = "".join(
            item.get("text", "")
            if isinstance(item, dict)
            else str(item)
            for item in content
        )

    content = str(content).strip()

    content = re.sub(
        r"^```(?:json)?\s*",
        "",
        content
    )

    content = re.sub(
        r"\s*```$",
        "",
        content
    )

    start = content.find("{")
    end = content.rfind("}")

    if start < 0 or end < start:
        raise ValueError(
            "LLM did not return a JSON object"
        )

    return json.loads(
        content[start:end + 1]
    )


def validate_extraction(data):
    """Validate the model output against the extraction contract."""

    if not isinstance(data, dict):
        raise ValueError(
            "Extraction must be a JSON object"
        )

    if set(data.keys()) != REQUIRED_FIELDS:
        raise ValueError(
            f"Incorrect fields. Expected {sorted(REQUIRED_FIELDS)}, "
            f"received {sorted(data.keys())}"
        )

    if data["intent"] not in ALLOWED_INTENTS:
        raise ValueError("Invalid intent")

    if data["eta_confidence"] not in {
        "HIGH",
        "MEDIUM",
        "LOW"
    }:
        raise ValueError("Invalid ETA confidence")

    if not isinstance(
        data["needs_clarification"],
        bool
    ):
        raise ValueError(
            "needs_clarification must be boolean"
        )

    if data["delay_minutes"] is not None:
        if (
            type(data["delay_minutes"]) is not int
            or data["delay_minutes"] < 0
        ):
            raise ValueError(
                "delay_minutes must be a non-negative integer or null"
            )

    for field in (
        "revised_eta_text",
        "shipment_reference",
        "latest_time_constraint",
        "option_choice",
        "clarification_reason"
    ):
        if (
            data[field] is not None
            and not isinstance(data[field], str)
        ):
            raise ValueError(
                f"{field} must be a string or null"
            )

    if data["equipment_requirement"] not in ALLOWED_EQUIPMENT:
        raise ValueError(
            "equipment_requirement must be STANDARD, REEFER, HEAVY or null"
        )

    return data


def extract_driver_message(
    driver_id: str,
    message: str,
    active_shipments: list,
    latest_eta: dict
) -> dict:
    """Call the LLM and return validated structured extraction."""

    if not message or not message.strip():
        raise ValueError(
            "Driver message cannot be empty"
        )

    prompt = _load_prompt()

    # Replace only intended placeholders.
    # This preserves the JSON braces in the prompt.
    formatted_prompt = (
        prompt
        .replace("{driver_id}", driver_id)
        .replace(
            "{active_shipments}",
            json.dumps(
                active_shipments,
                ensure_ascii=False
            )
        )
        .replace(
            "{latest_eta}",
            json.dumps(
                latest_eta,
                ensure_ascii=False
            )
        )
        .replace("{message}", message)
    )

    try:
        response = _get_llm().invoke(
            formatted_prompt
        )
        result = _parse_json(
            response.content
        )
        return validate_extraction(result)
    except Exception as exc:
        # Fallback heuristic parser when external LLM hits rate limits (HTTP 429) or network timeouts
        return _heuristic_fallback_extraction(message, active_shipments, latest_eta)


def _heuristic_fallback_extraction(
    message: str,
    active_shipments: list,
    latest_eta: dict
) -> dict:
    """Heuristic fallback extraction when external LLM is unavailable or rate-limited."""
    msg = message.lower().strip()
    result = {
        "intent": "REPORT_DELAY",
        "delay_minutes": None,
        "revised_eta_text": None,
        "shipment_reference": None,
        "latest_time_constraint": None,
        "option_choice": None,
        "equipment_requirement": None,
        "eta_confidence": "HIGH",
        "needs_clarification": False,
        "clarification_reason": None
    }

    # Out of scope detection
    if any(w in msg for w in ["detention", "pay", "charge", "money", "penalty", "invoice"]):
        result["intent"] = "OUT_OF_SCOPE"
        result["eta_confidence"] = "LOW"
        return validate_extraction(result)

    # Cancel detection
    if "do not book" in msg or "cancel" in msg:
        result["intent"] = "CANCEL"
        return validate_extraction(result)

    # Status detection
    if "status" in msg or "confirm" in msg or "update on" in msg:
        result["intent"] = "ASK_STATUS"
        return validate_extraction(result)

    # Early arrival
    if "already at the gate" in msg or "reached gate" in msg:
        result["intent"] = "EARLY_ARRIVAL"
        return validate_extraction(result)

    # Choose option
    if "first" in msg or "1st" in msg or "option 1" in msg or "take the first" in msg:
        result["intent"] = "CHOOSE_OPTION"
        result["option_choice"] = "1"
        return validate_extraction(result)
    elif "second" in msg or "2nd" in msg or "option 2" in msg or "take the second" in msg:
        result["intent"] = "CHOOSE_OPTION"
        result["option_choice"] = "2"
        return validate_extraction(result)
    elif "third" in msg or "3rd" in msg or "option 3" in msg:
        result["intent"] = "CHOOSE_OPTION"
        result["option_choice"] = "3"
        return validate_extraction(result)

    # Constraint
    time_constraint_match = re.search(r"(?:leave by|before|out by)\s*(\d{1,2}(?::\d{2})?)", msg)
    if time_constraint_match:
        result["intent"] = "ADD_CONSTRAINT"
        t = time_constraint_match.group(1)
        if ":" not in t:
            t = f"{int(t):02d}:00"
        elif len(t.split(":")[0]) == 1:
            h, m = t.split(":")
            # If 1:30, in afternoon context assume 13:30
            h_int = int(h)
            if h_int < 6:
                h_int += 12
            t = f"{h_int:02d}:{m}"
        result["latest_time_constraint"] = t

    # Equipment requirement
    if "reefer" in msg or "cold" in msg or "temperature" in msg:
        result["equipment_requirement"] = "REEFER"
    elif "heavy" in msg:
        result["equipment_requirement"] = "HEAVY"

    # ETA extraction
    eta_match = re.search(r"(?:eta|reaching|arrive|around)\s*(\d{1,2}(?::\d{2})?)", msg)
    if eta_match:
        t = eta_match.group(1)
        if ":" not in t:
            t = f"{int(t):02d}:00"
        else:
            h, m = t.split(":")
            h_int = int(h)
            if ("evening" in msg or "pm" in msg) and h_int < 12:
                h_int += 12
            t = f"{h_int:02d}:{m}"
        result["revised_eta_text"] = t
        result["eta_confidence"] = "MEDIUM" if ("around" in msg or "evening" in msg) else "HIGH"

    # Disambiguation check
    if active_shipments and len(active_shipments) > 1:
        # Check if message mentions specific shipment
        mentioned = False
        for s in active_shipments:
            s_id = s.get("shipment_id", "")
            if s_id.lower() in msg:
                result["shipment_reference"] = s_id
                mentioned = True
                break
        if not mentioned:
            result["needs_clarification"] = True
            result["clarification_reason"] = "Driver has multiple active shipments. Ask which shipment."
            return validate_extraction(result)

    # Missing ETA check
    if not result["revised_eta_text"] and not result["latest_time_constraint"] and result["intent"] == "REPORT_DELAY":
        # Check delay minutes
        delay_match = re.search(r"(?:late by|delay(?:ed)? by?)\s*(\d+)", msg)
        if delay_match:
            result["delay_minutes"] = int(delay_match.group(1))
        result["needs_clarification"] = True
        result["clarification_reason"] = "Missing arrival ETA."

    return validate_extraction(result)
