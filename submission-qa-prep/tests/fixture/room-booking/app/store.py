"""SQLite-backed booking store."""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS rooms (id TEXT PRIMARY KEY, open INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room TEXT NOT NULL REFERENCES rooms(id),
    owner TEXT NOT NULL,
    start_utc INTEGER NOT NULL,  -- epoch seconds
    end_utc INTEGER NOT NULL
);
"""


def connect(path=":memory:"):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn
