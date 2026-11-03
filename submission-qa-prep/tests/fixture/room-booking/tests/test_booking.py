import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import booking, slots, store  # noqa: E402

KST = timezone(timedelta(hours=9))


def setup():
    conn = store.connect()
    conn.execute("INSERT INTO rooms(id) VALUES ('A')")
    return conn


class BookingTest(unittest.TestCase):
    def test_stored_in_utc(self):
        conn = setup()
        booking.create(conn, "A", "u1", datetime(2026, 1, 5, 10, tzinfo=KST), datetime(2026, 1, 5, 11, tzinfo=KST))
        (start,) = conn.execute("SELECT start_utc FROM bookings").fetchone()
        self.assertEqual(datetime.fromtimestamp(start, timezone.utc).hour, 1)

    def test_back_to_back_allowed(self):
        conn = setup()
        d = lambda h: datetime(2026, 1, 5, h, tzinfo=KST)  # noqa: E731
        booking.create(conn, "A", "u1", d(10), d(11))
        booking.create(conn, "A", "u2", d(11), d(12))

    def test_overlap_rejected(self):
        conn = setup()
        d = lambda h, m=0: datetime(2026, 1, 5, h, m, tzinfo=KST)  # noqa: E731
        booking.create(conn, "A", "u1", d(10), d(11))
        with self.assertRaises(ValueError):
            booking.create(conn, "A", "u2", d(10, 30), d(11, 30))

    def test_free_slots_skip_booked(self):
        conn = setup()
        d = lambda h: datetime(2026, 1, 5, h, tzinfo=KST)  # noqa: E731
        booking.create(conn, "A", "u1", d(10), d(11))
        s = booking.to_utc(d(9))
        free = slots.free_slots(conn, "A", s, s + 4 * 3600)
        self.assertEqual(len(free), 6)


if __name__ == "__main__":
    unittest.main()
