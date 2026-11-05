# Extraction prompt

Read the driver message and the context. Reply with JSON only, matching this schema exactly.

{
  "intent": "REPORT_DELAY | ASK_OPTIONS | ADD_CONSTRAINT | CHOOSE_OPTION | CHANGE_MIND | ASK_STATUS | EARLY_ARRIVAL | CANCEL | OUT_OF_SCOPE | OTHER",
  "delay_minutes": <integer or null>,
  "revised_eta_text": "<time as written by the driver, or null>",
  "shipment_reference": "<shipment id or order reference if mentioned, else null>",
  "latest_time_constraint": "<time or phrase, or null>",
  "option_choice": "<which option, or null>",
  "eta_confidence": "HIGH | MEDIUM | LOW",
  "needs_clarification": <true or false>,
  "clarification_reason": "<one short sentence, or empty string>"
}

Rules
- A repair duration is not an arrival time. If the driver gives only a repair time, set revised_eta_text to null and needs_clarification to true.
- A range ("1 to 3 hours") is LOW confidence.
- If the driver has more than one active shipment and none is named, needs_clarification is true with reason "which shipment".
- Do not add fields. Do not explain.

Context:
Driver id: {driver_id}
Active shipments: {active_shipments}
Latest known ETA: {latest_eta}

Driver message:
{message}
