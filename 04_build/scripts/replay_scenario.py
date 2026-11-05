"""Replay the simultaneous-request scenario against a COPY of the database.

Run: python 04_build/scripts/replay_scenario.py
It fires N holds for the same slot at once and prints who won, then shows the slot's appointment rows.
Use it in the demo to prove the system cannot double-book.
"""
import os, shutil, sqlite3, sys, tempfile, threading

SRC = os.path.join(os.path.dirname(__file__), "..", "..", "data", "skyways_freight_operations.db")
CONTENDERS = ["SHP1012", "SHP1013", "SHP1014", "SHP1006"]   # delayed trucks competing for standard docks


def main():
    tmp = tempfile.mkdtemp(); path = os.path.join(tmp, "replay.db"); shutil.copy(SRC, path)
    con = sqlite3.connect(path)
    slot = con.execute("""select slot_id, slot_start_ts, dock_code from v_slot_availability
                          where facility_id='FAC-JAI-01' and dock_type='STANDARD' and availability_status='AVAILABLE'
                            and slot_start_ts >= '2026-08-04T12:00:00+05:30' order by slot_start_ts limit 1""").fetchone()
    con.close()
    print(f"Contested slot: {slot[0]} on {slot[2]} starting {slot[1]}")
    results = []

    def attempt(shp):
        c = sqlite3.connect(path, isolation_level=None, timeout=5)
        try:
            c.execute("BEGIN IMMEDIATE")
            c.execute("""insert into appointments(appointment_id, shipment_id, slot_id, appointment_status, booking_source,
                         is_current, booked_at, updated_at) values (?,?,?,'PENDING_CONFIRMATION','DRIVER_CHAT',1,
                         '2026-08-04T10:31:00+05:30','2026-08-04T10:31:00+05:30')""", (f"APT-RPL-{shp}", shp, slot[0]))
            c.execute("COMMIT"); results.append((shp, "HELD"))
        except sqlite3.IntegrityError as e:
            c.execute("ROLLBACK"); results.append((shp, f"REJECTED ({str(e)[:40]})"))
        finally:
            c.close()

    threads = [threading.Thread(target=attempt, args=(s,)) for s in CONTENDERS]
    for t in threads: t.start()
    for t in threads: t.join()
    for shp, outcome in results: print(f"  {shp}: {outcome}")
    con = sqlite3.connect(path)
    rows = con.execute("select appointment_id, shipment_id, appointment_status from appointments where slot_id=?", (slot[0],)).fetchall()
    print("Appointments on the slot now:", rows)
    held = [r for r in results if r[1] == "HELD"]
    print("RESULT:", "PASS, exactly one hold" if len(held) == 1 else "FAIL")
    shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
