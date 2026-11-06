\### Hold expiry persistence



Temporary appointment holds use a dedicated SQLite `appointment\_holds` table linked to appointments by `appointment\_id`.



The table records `created\_at`, `expires\_at`, and `hold\_status` (ACTIVE, EXPIRED, RELEASED).



The conversation state may carry `hold\_expires\_at` for agent replies, but SQLite remains the authoritative source for hold expiry.



A maintenance operation releases expired holds by cancelling their PENDING\_CONFIRMATION appointments and marking the corresponding hold records EXPIRED.



This design survives agent restarts, preserves appointment history, and supports auditing. The existing unique indexes remain the final protection against concurrent active bookings.

