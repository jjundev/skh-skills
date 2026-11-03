"""Free 30-minute slots for a room within a UTC window."""
SLOT = 30 * 60


def free_slots(conn, room, day_start_utc, day_end_utc):
    busy = conn.execute(
        "SELECT start_utc, end_utc FROM bookings WHERE room=? AND end_utc > ? AND start_utc < ?",
        (room, day_start_utc, day_end_utc),
    ).fetchall()
    out = []
    t = day_start_utc
    while t + SLOT <= day_end_utc:
        if not any(s < t + SLOT and t < e for s, e in busy):
            out.append(t)
        t += SLOT
    return out
