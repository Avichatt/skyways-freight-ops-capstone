"""The one test the panel will ask about: two holds on one slot, only one survives.

Run: pytest tests/test_no_double_booking.py -q
It works on a COPY of the database so your demo state is untouched.
"""
import os, shutil, sqlite3, tempfile, threading
import pytest

SRC = os.path.join(os.path.dirname(__file__), "..", "data", "skyways_freight_operations.db")


@pytest.fixture
def db_copy():
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp, "copy.db")
    shutil.copy(SRC, dst)
    yield dst
    try:
        shutil.rmtree(tmp)
    except Exception:
        pass


def _free_slot(path):
    con = sqlite3.connect(path)
    row = con.execute("""select slot_id from v_slot_availability
                         where facility_id='FAC-JAI-01' and dock_type='STANDARD'
                           and availability_status='AVAILABLE' order by slot_start_ts limit 1""").fetchone()
    con.close()
    return row[0]


def _try_hold(path, slot_id, shipment_id, results):
    con = sqlite3.connect(path, isolation_level=None, timeout=5)
    con.execute("PRAGMA foreign_keys = ON")
    try:
        con.execute("BEGIN IMMEDIATE")
        con.execute("""insert into appointments(appointment_id, shipment_id, slot_id, appointment_status, booking_source,
                                                is_current, booked_at, updated_at)
                       values (?, ?, ?, 'PENDING_CONFIRMATION', 'DRIVER_CHAT', 1, '2026-08-04T10:30:00+05:30', '2026-08-04T10:30:00+05:30')""",
                    (f"APT-TEST-{shipment_id}", shipment_id, slot_id))
        con.execute("COMMIT")
        results.append((shipment_id, True))
    except sqlite3.IntegrityError:
        con.execute("ROLLBACK")
        results.append((shipment_id, False))
    finally:
        con.close()


def test_only_one_active_appointment_per_slot(db_copy):
    slot = _free_slot(db_copy)
    results = []
    # SHP1012 and SHP1013 have no current active appointment in the seed, so both are valid contenders.
    t1 = threading.Thread(target=_try_hold, args=(db_copy, slot, "SHP1012", results))
    t2 = threading.Thread(target=_try_hold, args=(db_copy, slot, "SHP1013", results))
    t1.start(); t2.start(); t1.join(); t2.join()
    wins = [s for s, ok in results if ok]
    assert len(wins) == 1, f"expected exactly one winner, got {results}"
    con = sqlite3.connect(db_copy)
    n = con.execute("""select count(*) from appointments where slot_id=? and is_current=1
                       and appointment_status in ('PENDING_CONFIRMATION','CONFIRMED','IN_PROGRESS')""", (slot,)).fetchone()[0]
    con.close()
    assert n == 1


# TODO (Intermediate level): add a test where the loser is offered a fresh option list that no longer contains the taken slot.
# TODO (Enterprise level): add a test that an expired hold is released and the slot becomes AVAILABLE again.
