"""Typed tool contracts for the SkyWays agent.

Every tool reads or writes the SQLite system of record and returns plain dictionaries.
The LLM never touches SQL. The LLM decides WHICH tool to call and WHAT to say; the tools decide WHAT IS TRUE.

Finished for you: get_driver_context, get_latest_eta.
Left for you with guidance: find_feasible_slots, hold_slot, request_confirmation, get_request_status, escalate.
"""
import os, sqlite3
from datetime import datetime, timedelta
from typing import Optional

DB = os.getenv("SKYWAYS_DB_PATH", "data/skyways_freight_operations.db")


def _con() -> sqlite3.Connection:
    con = sqlite3.connect(DB, isolation_level=None)   # autocommit; use explicit BEGIN IMMEDIATE for writes
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def get_driver_context(driver_id: str) -> dict:
    """Return the driver's active shipments with destination, booked slot and latest ETA.

    More than one row means the conversation must disambiguate before anything else.
    """
    con = _con()
    rows = con.execute(
        """
        select shipment_id, destination_facility_id, priority_code, required_dock_type,
               expected_unload_min, current_status, effective_eta_ts, eta_source,
               appointment_id, slot_id, slot_start_ts, slot_end_ts, planned_dock_code
        from v_inbound_operational_state
        where driver_id = ? and current_status in ('ASSIGNED','IN_TRANSIT','AT_GATE','WAITING')
        order by slot_start_ts
        """, (driver_id,)).fetchall()
    return {"driver_id": driver_id, "active_shipments": [dict(r) for r in rows], "needs_disambiguation": len(rows) > 1}


def get_latest_eta(shipment_id: str) -> dict:
    """Return the effective ETA, where it came from and how confident it is."""
    r = _con().execute("select * from v_latest_eta where shipment_id = ?", (shipment_id,)).fetchone()
    return dict(r) if r else {"shipment_id": shipment_id, "error": "unknown shipment"}


def find_feasible_slots(shipment_id: str, not_before_ts: str, latest_leave_ts: Optional[str] = None, limit: int = 3) -> list[dict]:
    """Return up to `limit` slots the truck can actually use.

    A slot is feasible only when ALL of these hold (see brief, section "Slot feasibility"):
      1. slot_start_ts >= not_before_ts (the truck can reach the gate before the window opens)
      2. the dock type matches shipment.required_dock_type (ANY matches STANDARD; REEFER and HEAVY are strict)
      3. v_slot_availability.availability_status == 'AVAILABLE'
      4. expected_unload_min fits between slot_start_ts and slot_end_ts
      5. slot_start_ts is before the facility's LAST_NEW_START_TIME rule (facility_rules)
      6. if latest_leave_ts is given, slot_start_ts + expected_unload_min <= latest_leave_ts

    TODO: implement with one SQL query plus Python checks. Return a list of SlotOption-shaped dicts.
    Hint: start from v_slot_availability joined to shipments; the facility rules table carries the 21:00 rule.
    Trap: do not filter on slot_status alone; a slot can be OPEN and still have an active appointment.
    """
    raise NotImplementedError


def hold_slot(slot_id: str, shipment_id: str, hold_minutes: int = 10) -> dict:
    """Create a PENDING_CONFIRMATION appointment for the slot, or fail cleanly if someone else holds it.

    The database index ux_active_appointment_per_slot allows only one active appointment per slot.
    A second insert raises sqlite3.IntegrityError. Catch it and return {"held": False, "reason": "slot taken"}.

    TODO: implement. Use `BEGIN IMMEDIATE` so two holds cannot interleave.
    Set is_current = 1, booking_source = 'DRIVER_CHAT', booked_at = now, and record the expiry in your state
    (the schema has no expiry column on purpose; decide where it lives and defend the decision in an ADR).
    """
    raise NotImplementedError


def request_confirmation(appointment_id: str) -> dict:
    """Ask the warehouse to confirm. In the classroom this writes an operational_messages row.

    A request is not a confirmation. The driver must be told the slot is pending until confirmed.
    TODO: implement. Return {"appointment_id":..., "status": "PENDING_CONFIRMATION", "message_id":...}.
    """
    raise NotImplementedError


def get_request_status(appointment_id: str) -> dict:
    """Return appointment_status and the latest warehouse reply, if any (operational_messages)."""
    raise NotImplementedError


def escalate(thread_id: str, reason: str) -> dict:
    """Mark the thread for human review and return what the driver should be told.

    Use this when: no feasible slot exists, the driver's ETA confidence is LOW after two clarifications,
    the message is OUT_OF_SCOPE, or a priority conflict needs a planner.
    TODO: implement (update chat_threads.thread_status, insert an operational_messages row).
    """
    raise NotImplementedError


def release_expired_holds(now_ts: str) -> int:
    """Cancel PENDING_CONFIRMATION appointments whose hold has expired. Return how many were released.

    TODO: implement once you have decided where hold expiry lives.
    """
    raise NotImplementedError


if __name__ == "__main__":
    print(get_driver_context("DRV004"))      # expected: two active shipments, needs_disambiguation True
    print(get_latest_eta("SHP1006"))          # expected: the 11:20 driver-declared ETA, not the 10:50 one
