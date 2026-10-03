"""Database policy shared by runtime and release checks."""
import sqlite3

def configure_connection(conn: sqlite3.Connection) -> sqlite3.Connection:
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
