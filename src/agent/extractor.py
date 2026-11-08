
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

    response = _get_llm().invoke(
        formatted_prompt
    )

    result = _parse_json(
        response.content
    )

    return validate_extraction(result)
