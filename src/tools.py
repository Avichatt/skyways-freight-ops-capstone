"""
Typed tool contracts for the SkyWays agent.

Every tool reads or writes the SQLite system of record and returns plain
dictionaries.

The LLM never touches SQL. The LLM decides WHICH tool to call and WHAT to say;
the tools decide WHAT IS TRUE.

Finished for you:
    - get_driver_context
    - get_latest_eta

Left for you with guidance:
    - find_feasible_slots
    - hold_slot
    - request_confirmation
    - get_request_status
    - escalate
"""

import os
import json
import sqlite3
import urllib.request
import urllib.error

from datetime import datetime, timedelta
from typing import Optional


DB = os.getenv(
    "SKYWAYS_DB_PATH",
    "data/skyways_freight_operations.db"
)


def _con() -> sqlite3.Connection:
    con = sqlite3.connect(
        DB,
        isolation_level=None
    )  # autocommit

    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def predict_unload_duration(
    shipment: dict,
    candidate: dict
) -> dict:
    """
    Call the unloading predictor.
    Falls back safely if unavailable.
    """

    url = os.getenv(
        "PREDICTOR_URL",
        "http://127.0.0.1:8000/predict"
    )

    payload = {
        "shipment_id": shipment["shipment_id"],
        "facility_id": shipment["destination_facility_id"],
        "dock_type": candidate["dock_type"],
        "pallet_count": shipment["pallet_count"],
        "load_weight_kg": shipment["load_weight_kg"],
        "priority_code": shipment["priority_code"],
        "origin_distance_km": 0,
        "planned_departure_ts": shipment["planned_departure_ts"],
        "carrier_id": shipment["carrier_id"],
        "candidate_slot_start_ts": candidate["slot_start_ts"],
    }

    try:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json"
            },
            method="POST",
        )

        with urllib.request.urlopen(
            request,
            timeout=0.3
        ) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        return {
            "unload_p90_min": int(
                result["unload_p90_min"]
            ),
            "predicted_unload_min": int(
                result["predicted_unload_min"]
            ),
            "model_version": result["model_version"],
            "prediction_fallback": False,
        }

    except Exception as exc:
        return {
            "unload_p90_min": int(
                shipment["expected_unload_min"]
            ),
            "predicted_unload_min": int(
                shipment["expected_unload_min"]
            ),
            "model_version": None,
            "prediction_fallback": True,
            "fallback_reason": str(exc),
        }


def get_driver_context(driver_id: str) -> dict:
    """
    Return the driver's active shipments with destination, booked slot
    and latest ETA.

    More than one row means the conversation must disambiguate before
    anything else.
    """

    con = _con()

    rows = con.execute(
        """
        SELECT
            shipment_id,
            destination_facility_id,
            priority_code,
            required_dock_type,
            expected_unload_min,
            current_status,
            effective_eta_ts,
            eta_source,
            appointment_id,
            slot_id,
            slot_start_ts,
            slot_end_ts,
            planned_dock_code
        FROM v_inbound_operational_state
        WHERE driver_id = ?
          AND current_status IN (
                'ASSIGNED',
                'IN_TRANSIT',
                'AT_GATE',
                'WAITING'
          )
        ORDER BY slot_start_ts
        """,
        (driver_id,)
    ).fetchall()

    return {
        "driver_id": driver_id,
        "active_shipments": [
            dict(r) for r in rows
        ],
        "needs_disambiguation": len(rows) > 1,
    }


def get_latest_eta(shipment_id: str) -> dict:
    """
    Return the effective ETA,
    where it came from and
    how confident it is.
    """

    row = _con().execute(
        """
        SELECT *
        FROM v_latest_eta
        WHERE shipment_id = ?
        """,
        (shipment_id,)
    ).fetchone()

    return (
        dict(row)
        if row
        else {
            "shipment_id": shipment_id,
            "error": "unknown shipment",
        }
    )


def find_feasible_slots(
    shipment_id: str,
    not_before_ts: str,
    latest_leave_ts: Optional[str] = None,
    limit: int = 3,
) -> list[dict]:
    """
    Return up to `limit` slots the truck can actually use.

    A slot is feasible only when ALL of these hold:

    1. slot_start_ts >= not_before_ts
    2. dock type matches shipment.required_dock_type
    3. availability_status == 'AVAILABLE'
    4. required unload duration fits in slot window
    5. facility LAST_NEW_START_TIME rule respected
    6. latest_leave_ts respected if given

    TODO:
        Implement with SQL + Python checks.

    Hint:
        Start from v_slot_availability joined to shipments.

    Trap:
        Do not filter on slot_status alone.
    """

    raise NotImplementedError


def hold_slot(
    slot_id: str,
    shipment_id: str,
    hold_minutes: int = 10,
) -> dict:
    """
    Create a PENDING_CONFIRMATION appointment.

    Use BEGIN IMMEDIATE so concurrent holds cannot interleave.

    Catch IntegrityError and return:

    {
        "held": False,
        "reason": "slot taken"
    }
    """

    raise NotImplementedError


def request_confirmation(
    appointment_id: str
) -> dict:
    """
    Ask warehouse to confirm.

    Classroom version writes an operational_messages row.

    Return:

    {
        "appointment_id": ...,
        "status": "PENDING_CONFIRMATION",
        "message_id": ...
    }
    """

    raise NotImplementedError


def get_request_status(
    appointment_id: str
) -> dict:
    """
    Return appointment status and latest warehouse reply.
    """

    raise NotImplementedError


def escalate(
    thread_id: str,
    reason: str
) -> dict:
    """
    Mark thread for human review.

    Used when:
        - No feasible slot exists
        - ETA confidence remains LOW
        - OUT_OF_SCOPE request
        - Planner intervention required

    TODO:
        Update chat_threads.thread_status
        Insert operational_messages row
    """

    raise NotImplementedError


def release_expired_holds(
    now_ts: str
) -> int:
    """
    Cancel expired PENDING_CONFIRMATION appointments.

    Return number released.
    """

    raise NotImplementedError


if __name__ == "__main__":

    print(
        get_driver_context("DRV004")
    )

    print(
        get_latest_eta("SHP1006")
    )