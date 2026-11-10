"""Freeze the database for the demo and restore it afterwards.

python 04_build/scripts/snapshot_db.py save    -> copies data/skyways_freight_operations.db to data/demo_snapshot.db
python 04_build/scripts/snapshot_db.py restore -> copies it back
Run `save` before you rehearse, `restore` after every rehearsal, so the demo always starts from the same state.
"""
import os, shutil, sys
ROOT = os.path.join(os.path.dirname(__file__), "..", "data")
LIVE, SNAP = os.path.join(ROOT, "skyways_freight_operations.db"), os.path.join(ROOT, "demo_snapshot.db")
cmd = sys.argv[1] if len(sys.argv) > 1 else ""
if cmd == "save":
    shutil.copy(LIVE, SNAP); print("saved", SNAP)
elif cmd == "restore":
    shutil.copy(SNAP, LIVE); print("restored", LIVE)
else:
    print("usage: snapshot_db.py save | restore")
