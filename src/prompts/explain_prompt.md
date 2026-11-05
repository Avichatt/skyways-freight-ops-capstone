# Explanation prompt (driver-facing reply)

Write the reply to the driver using only the facts below. Plain words, at most five short lines.
Say the commitment status in the first line. If options are listed, number them and give dock, start time and whether unloading fits before the driver's latest leave time.
If something was escalated, say who will contact the driver and roughly when.

Commitment status: {commitment_status}
Facility: {facility_name}
Options: {options}
Held slot and expiry: {held}
Escalation reason: {escalation_reason}
Driver's constraint: {latest_leave}
