"""Create/cancel bookings. Overlap is checked in Python before insert."""
from datetime import datetime, timezone

MAX_SECONDS = 4 * 3600


def to_utc(dt):
    # Naive datetimes are rejected so local time never sneaks into storage.
    if dt.tzinfo is None:
        raise ValueError("timezone-aware datetime required")
    return int(dt.astimezone(timezone.utc).timestamp())


def overlaps(conn, room, start, end):
    row = conn.execute(
        "SELECT 1 FROM bookings WHERE room=? AND start_utc < ? AND ? < end_utc LIMIT 1",
        (room, end, start),
    ).fetchone()
    return row is not None


def create(conn, room, owner, start_dt, end_dt):
    start, end = to_utc(start_dt), to_utc(end_dt)
    if end <= start or end - start > MAX_SECONDS:
        raise ValueError("invalid duration")
    is_open = conn.execute("SELECT open FROM rooms WHERE id=?", (room,)).fetchone()
    if not is_open or not is_open[0]:
        raise ValueError("room closed")
    if overlaps(conn, room, start, end):
        raise ValueError("overlap")
    cur = conn.execute(
        "INSERT INTO bookings(room, owner, start_utc, end_utc) VALUES (?,?,?,?)",
        (room, owner, start, end),
    )
    conn.commit()
    return cur.lastrowid


def close_room(conn, room, now_dt):
    now = to_utc(now_dt)
    conn.execute("UPDATE rooms SET open=0 WHERE id=?", (room,))
    conn.execute("DELETE FROM bookings WHERE room=? AND start_utc >= ?", (room, now))
    conn.commit()
