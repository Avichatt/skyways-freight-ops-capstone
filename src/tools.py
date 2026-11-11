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


_LOCAL_MODEL = None
_LOCAL_MODEL_LOADED = False

def _get_local_model():
    global _LOCAL_MODEL, _LOCAL_MODEL_LOADED
    if not _LOCAL_MODEL_LOADED:
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model", "unload_predictor.joblib")
        if os.path.exists(model_path):
            try:
                import joblib
                _LOCAL_MODEL = joblib.load(model_path)
            except Exception:
                pass
        _LOCAL_MODEL_LOADED = True
    return _LOCAL_MODEL


def predict_unload_duration(
    shipment: dict,
    candidate: dict
) -> dict:
    """
    Call the unloading predictor behind the integration contract.
    Budget: 300 ms. Falls back safely if unavailable or timed out.
    """
    url = os.getenv("PREDICTOR_URL", "http://127.0.0.1:8000/predict")
    payload = {
        "shipment_id": shipment["shipment_id"],
        "facility_id": shipment["destination_facility_id"],
        "dock_type": candidate["dock_type"],
        "pallet_count": shipment.get("pallet_count"),
        "load_weight_kg": shipment["load_weight_kg"],
        "priority_code": shipment["priority_code"],
        "origin_distance_km": shipment.get("origin_distance_km", 0) or 0,
        "planned_departure_ts": shipment.get("planned_departure_ts") or "2026-08-04T06:00:00+05:30",
        "carrier_id": shipment["carrier_id"],
        "candidate_slot_start_ts": candidate["slot_start_ts"],
    }

    # 1. Try HTTP service with 300 ms timeout
    try:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=0.3) as response:
            result = json.loads(response.read().decode("utf-8"))
        return {
            "unload_p90_min": int(result["unload_p90_min"]),
            "predicted_unload_min": int(result["predicted_unload_min"]),
            "late_arrival_probability": float(result.get("late_arrival_probability", 0.0)),
            "model_version": result.get("model_version", "rf-2026-08-04"),
            "prediction_fallback": False,
        }
    except Exception:
        pass

    # 2. Try in-process model artifact if HTTP server not running
    local_mdl = _get_local_model()
    if local_mdl is not None:
        try:
            import pandas as pd
            dep_ts = payload["planned_departure_ts"]
            slot_ts = payload["candidate_slot_start_ts"]
            dep_dt = datetime.fromisoformat(dep_ts)
            slot_dt = datetime.fromisoformat(slot_ts)
            row = {
                "dock_type": payload["dock_type"],
                "facility_id": payload["facility_id"],
                "carrier_id": payload["carrier_id"],
                "vehicle_type_code": "20FT",
                "product_category": "Standard freight",
                "priority_code": payload["priority_code"],
                "origin_city": "Delhi NCR",
                "day_of_week": slot_dt.strftime("%A"),
                "temperature_control_required": 1 if payload["dock_type"] == "REEFER" else 0,
                "load_weight_kg": payload["load_weight_kg"],
                "pallet_count": payload["pallet_count"],
                "origin_distance_km": payload["origin_distance_km"],
                "rain_flag": 0,
                "labour_shortage_flag": 0,
                "departure_hour": dep_dt.hour,
                "arrival_hour": slot_dt.hour,
                "slot_hour": slot_dt.hour,
                "arrival_month": slot_dt.month,
            }
            df = pd.DataFrame([row])
            pred_val = float(local_mdl.predict(df)[0])
            pred_min = max(20, int(round(pred_val)))
            p90_min = pred_min + 14
            return {
                "unload_p90_min": p90_min,
                "predicted_unload_min": pred_min,
                "late_arrival_probability": 0.2,
                "model_version": "rf-2026-08-04",
                "prediction_fallback": False,
            }
        except Exception:
            pass

    # 3. Pure fallback to database default
    expected = int(shipment.get("expected_unload_min") or 45)
    return {
        "unload_p90_min": expected,
        "predicted_unload_min": expected,
        "late_arrival_probability": 0.0,
        "model_version": None,
        "prediction_fallback": True,
        "fallback_reason": "predictor timeout or offline, database fallback used",
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


def _parse_iso_or_time(time_str: str, base_date: str = "2026-08-04") -> datetime:
    """Robust parser for ISO timestamps or driver-stated times."""
    import re
    s = str(time_str).strip()
    try:
        if "T" in s and len(s) >= 19:
            return datetime.fromisoformat(s)
    except Exception:
        pass

    match = re.search(r"(\d{1,2})(?::(\d{2}))?", s)
    if match:
        hh = int(match.group(1))
        mm = int(match.group(2)) if match.group(2) else 0
        if hh < 6:  # e.g., 1:30 PM is 13:30
            hh += 12
        return datetime.fromisoformat(f"{base_date}T{hh:02d}:{mm:02d}:00+05:30")

    return datetime.fromisoformat(f"{base_date}T00:00:00+05:30")


def find_feasible_slots(
    shipment_id: str,
    not_before_ts: str,
    latest_leave_ts: Optional[str] = None,
    limit: int = 3,
    required_dock_type_override: Optional[str] = None,
) -> list[dict]:
    """
    Return up to `limit` slots the truck can actually use.

    A slot is feasible only when ALL of these hold:
    1. slot_start_ts >= not_before_ts
    2. dock type matches shipment.required_dock_type (and weight constraints)
    3. availability_status == 'AVAILABLE'
    4. required unload duration fits in slot window (tested with unload_p90_min)
    5. facility LAST_NEW_START_TIME rule respected (starts before cutoff, default 21:00)
    6. latest_leave_ts respected if given (slot ends before leave time)
    """
    con = _con()
    ship_row = con.execute(
        "SELECT * FROM shipments WHERE shipment_id = ?",
        (shipment_id,)
    ).fetchone()

    if not ship_row:
        return []

    shipment = dict(ship_row)
    facility_id = shipment["destination_facility_id"]
    req_dock = required_dock_type_override or shipment["required_dock_type"]
    load_weight = shipment["load_weight_kg"]
    expected_unload = shipment["expected_unload_min"]

    # Base date from shipment or default
    base_date = "2026-08-04"
    if shipment.get("latest_eta_ts"):
        base_date = shipment["latest_eta_ts"][:10]

    not_before_dt = _parse_iso_or_time(not_before_ts, base_date=base_date)

    # Facility rules
    rules = con.execute(
        "SELECT rule_type, rule_value FROM facility_rules WHERE facility_id = ? AND active_flag = 1",
        (facility_id,)
    ).fetchall()
    rules_dict = {r["rule_type"]: r["rule_value"] for r in rules}
    last_new_start_str = rules_dict.get("LAST_NEW_START_TIME", "21:00")
    last_start_hour, last_start_min = [int(x) for x in last_new_start_str.split(":")[:2]]

    leave_dt = None
    if latest_leave_ts:
        leave_dt = _parse_iso_or_time(latest_leave_ts, base_date=base_date)

    # Query all AVAILABLE slots for the facility ordered by time then dock
    slots = con.execute(
        """
        SELECT
            slot_id,
            facility_id,
            dock_code,
            dock_type,
            supports_refrigerated,
            max_vehicle_weight_kg,
            slot_start_ts,
            slot_end_ts,
            availability_status
        FROM v_slot_availability
        WHERE facility_id = ?
          AND availability_status = 'AVAILABLE'
        ORDER BY slot_start_ts, dock_code
        """,
        (facility_id,)
    ).fetchall()

    feasible_options = []

    for s_row in slots:
        cand = dict(s_row)
        slot_start_dt = datetime.fromisoformat(cand["slot_start_ts"])
        slot_end_dt = datetime.fromisoformat(cand["slot_end_ts"])

        # 1. slot_start_ts >= not_before_ts
        if slot_start_dt < not_before_dt:
            continue

        # 2. Dock type and vehicle weight compatibility
        if req_dock == "REEFER":
            if cand["dock_type"] != "REEFER" and cand.get("supports_refrigerated") != 1:
                continue
        elif req_dock == "HEAVY":
            if cand["dock_type"] != "HEAVY":
                continue
            if cand.get("max_vehicle_weight_kg") and load_weight > cand["max_vehicle_weight_kg"]:
                continue
        else:  # STANDARD
            if load_weight > 25000:
                if cand["dock_type"] != "HEAVY":
                    continue
            elif cand["dock_type"] != "STANDARD":
                continue

        # 3. availability_status == 'AVAILABLE' (filtered by query and double-checked)
        if cand["availability_status"] != "AVAILABLE":
            continue

        # 4. Required unload duration fits in slot window
        window_min = (slot_end_dt - slot_start_dt).total_seconds() / 60
        pred = predict_unload_duration(shipment, cand)
        unload_p90 = pred.get("unload_p90_min", expected_unload)
        if unload_p90 > window_min:
            continue

        # 5. LAST_NEW_START_TIME rule (no new operation should start after cutoff)
        cutoff_dt = slot_start_dt.replace(hour=last_start_hour, minute=last_start_min, second=0)
        if slot_start_dt > cutoff_dt:
            continue

        # 6. latest_leave_ts respected if given
        if leave_dt and slot_end_dt > leave_dt:
            continue

        feasible_options.append({
            "slot_id": cand["slot_id"],
            "dock_code": cand["dock_code"],
            "dock_type": cand["dock_type"],
            "slot_start_ts": cand["slot_start_ts"],
            "slot_end_ts": cand["slot_end_ts"],
            "fits_unload": True,
            "reason_shown": f"Available {cand['dock_type']} dock {cand['dock_code']} (p90 unload: {unload_p90}m)",
            "unload_p90_min": unload_p90,
        })

        if len(feasible_options) >= limit:
            break

    return feasible_options


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
    now_ts = os.getenv("SIMULATED_NOW", "2026-08-04T10:30:00+05:30")
    try:
        now_dt = datetime.fromisoformat(now_ts)
    except Exception:
        now_dt = datetime(2026, 8, 4, 10, 30, 0)
    expires_dt = now_dt + timedelta(minutes=hold_minutes)
    expires_ts = expires_dt.isoformat()

    con = _con()
    try:
        con.execute("BEGIN IMMEDIATE")

        # Check existing active appointment for this shipment
        curr_row = con.execute(
            "SELECT appointment_id FROM appointments WHERE shipment_id = ? AND is_current = 1",
            (shipment_id,)
        ).fetchone()
        replaced_id = curr_row["appointment_id"] if curr_row else None

        if replaced_id:
            con.execute(
                "UPDATE appointments SET is_current = 0, updated_at = ? WHERE appointment_id = ?",
                (now_ts, replaced_id)
            )

        import uuid
        apt_suffix = uuid.uuid4().hex[:6].upper()
        appointment_id = f"APT-{shipment_id}-{apt_suffix}"

        con.execute(
            """
            INSERT INTO appointments (
                appointment_id,
                shipment_id,
                slot_id,
                appointment_status,
                booking_source,
                is_current,
                booked_at,
                replaced_appointment_id,
                updated_at
            ) VALUES (?, ?, ?, 'PENDING_CONFIRMATION', 'DRIVER_CHAT', 1, ?, ?, ?)
            """,
            (appointment_id, shipment_id, slot_id, now_ts, replaced_id, now_ts)
        )
        con.execute("COMMIT")

        return {
            "held": True,
            "appointment_id": appointment_id,
            "slot_id": slot_id,
            "shipment_id": shipment_id,
            "hold_expires_at": expires_ts,
            "hold_minutes": hold_minutes,
        }

    except sqlite3.IntegrityError:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass
        return {
            "held": False,
            "reason": "slot taken",
        }
    except Exception as exc:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass
        return {
            "held": False,
            "reason": str(exc),
        }


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
    now_ts = os.getenv("SIMULATED_NOW", "2026-08-04T10:30:00+05:30")
    con = _con()
    apt_row = con.execute(
        "SELECT a.*, s.destination_facility_id FROM appointments a JOIN shipments s ON a.shipment_id = s.shipment_id WHERE a.appointment_id = ?",
        (appointment_id,)
    ).fetchone()

    if not apt_row:
        return {
            "appointment_id": appointment_id,
            "status": "ERROR",
            "error": f"Appointment {appointment_id} not found"
        }

    apt = dict(apt_row)
    facility_id = apt["destination_facility_id"]

    # Look up facility warehouse coordinator contact
    coord_row = con.execute(
        "SELECT email FROM facility_contacts WHERE facility_id = ? AND contact_role = 'WAREHOUSE_COORDINATOR' AND active_flag = 1",
        (facility_id,)
    ).fetchone()
    recipient_email = coord_row["email"] if coord_row and coord_row["email"] else "warehouse@skyways.example"

    import uuid
    msg_id = f"OM-{uuid.uuid4().hex[:6].upper()}"

    con.execute(
        """
        INSERT INTO operational_messages (
            operational_message_id,
            shipment_id,
            appointment_id,
            channel,
            sender_address,
            recipient_address,
            subject,
            message_body,
            sent_at,
            delivery_status
        ) VALUES (?, ?, ?, 'EMAIL', 'agent@skyways.example', ?, ?, ?, ?, 'SENT')
        """,
        (
            msg_id,
            apt["shipment_id"],
            appointment_id,
            recipient_email,
            f"Slot confirmation request for {apt['shipment_id']}",
            f"Driver accepted slot {apt['slot_id']}. Appointment {appointment_id} held with status PENDING_CONFIRMATION.",
            now_ts
        )
    )

    return {
        "appointment_id": appointment_id,
        "status": "PENDING_CONFIRMATION",
        "message_id": msg_id,
        "recipient": recipient_email
    }


def get_request_status(
    appointment_id: str
) -> dict:
    """
    Return appointment status and latest warehouse reply.
    """
    con = _con()
    apt_row = con.execute(
        "SELECT appointment_id, shipment_id, slot_id, appointment_status, booked_at, confirmed_at, updated_at FROM appointments WHERE appointment_id = ?",
        (appointment_id,)
    ).fetchone()

    if not apt_row:
        return {
            "appointment_id": appointment_id,
            "status": "UNKNOWN",
            "error": "Appointment not found"
        }

    apt = dict(apt_row)

    # Check for warehouse replies in operational_messages
    reply_row = con.execute(
        """
        SELECT message_body, delivery_status, sent_at
        FROM operational_messages
        WHERE appointment_id = ? AND delivery_status = 'REPLIED'
        ORDER BY sent_at DESC
        LIMIT 1
        """,
        (appointment_id,)
    ).fetchone()

    latest_reply = reply_row["message_body"] if reply_row else None

    return {
        "appointment_id": appointment_id,
        "shipment_id": apt["shipment_id"],
        "slot_id": apt["slot_id"],
        "appointment_status": apt["appointment_status"],
        "latest_warehouse_reply": latest_reply,
    }


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
    """
    now_ts = os.getenv("SIMULATED_NOW", "2026-08-04T10:30:00+05:30")
    con = _con()

    # Update chat_threads if exists
    thread_row = con.execute(
        "SELECT * FROM chat_threads WHERE thread_id = ?",
        (thread_id,)
    ).fetchone()

    shipment_id = None
    if thread_row:
        shipment_id = thread_row["shipment_id"]
        con.execute(
            "UPDATE chat_threads SET thread_status = 'ESCALATED' WHERE thread_id = ?",
            (thread_id,)
        )

    # Log operational message to operations
    import uuid
    msg_id = f"OM-ESC-{uuid.uuid4().hex[:6].upper()}"
    if shipment_id:
        con.execute(
            """
            INSERT INTO operational_messages (
                operational_message_id,
                shipment_id,
                appointment_id,
                channel,
                sender_address,
                recipient_address,
                subject,
                message_body,
                sent_at,
                delivery_status
            ) VALUES (?, ?, NULL, 'INTERNAL', 'agent@skyways.example', 'operations@skyways.example', ?, ?, ?, 'SENT')
            """,
            (
                msg_id,
                shipment_id,
                f"Thread {thread_id} Escalation: {reason}",
                f"Driver exception escalated: {reason}",
                now_ts
            )
        )

    return {
        "escalated": True,
        "thread_id": thread_id,
        "reason": reason,
        "contact_role": "OPERATIONS_COORDINATOR",
        "message": "Operations team will contact the driver within 15 minutes."
    }


def release_expired_holds(
    now_ts: str
) -> int:
    """
    Cancel expired PENDING_CONFIRMATION appointments.
    Return number released.
    """
    con = _con()
    # Any PENDING_CONFIRMATION appointment booked more than 10 minutes before now_ts
    # In classroom dataset, holds expire in 10 minutes.
    try:
        now_dt = datetime.fromisoformat(now_ts)
        cutoff_dt = now_dt - timedelta(minutes=10)
        cutoff_ts = cutoff_dt.isoformat()
    except Exception:
        cutoff_ts = now_ts

    cur = con.execute(
        """
        UPDATE appointments
        SET appointment_status = 'CANCELLED',
            cancelled_at = ?,
            cancellation_reason = 'HOLD_EXPIRED',
            updated_at = ?
        WHERE appointment_status = 'PENDING_CONFIRMATION'
          AND booked_at <= ?
        """,
        (now_ts, now_ts, cutoff_ts)
    )
    return cur.rowcount


if __name__ == "__main__":

    print(
        get_driver_context("DRV004")
    )

    print(
        get_latest_eta("SHP1006")
    )