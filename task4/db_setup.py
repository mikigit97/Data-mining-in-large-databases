"""
db_setup.py — Schema creation, data seeding, DB connection, and safe query execution.
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

_DB_PATH = Path(__file__).parent / "agency.db"

FORBIDDEN = re.compile(
    r'\b(drop|delete|insert|update|alter|create|attach|pragma|vacuum|reindex)\b',
    re.IGNORECASE,
)


@st.cache_resource
def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    create_schema(conn)
    seed_data(conn)
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS suspects (
            suspect_id      INTEGER PRIMARY KEY,
            name            TEXT    NOT NULL,
            age             INTEGER NOT NULL,
            occupation      TEXT    NOT NULL,
            district        TEXT    NOT NULL,
            motive_score    INTEGER NOT NULL,
            known_associate TEXT
        );

        CREATE TABLE IF NOT EXISTS crimes (
            crime_id        INTEGER PRIMARY KEY,
            crime_type      TEXT    NOT NULL,
            district        TEXT    NOT NULL,
            reported_date   TEXT    NOT NULL,
            status          TEXT    NOT NULL,
            severity        INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS evidence (
            evidence_id     INTEGER PRIMARY KEY,
            crime_id        INTEGER NOT NULL,
            suspect_id      INTEGER NOT NULL,
            evidence_type   TEXT    NOT NULL,
            strength        INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS detective_log (
            session_id      TEXT    NOT NULL,
            level_num       INTEGER NOT NULL,
            completed       INTEGER NOT NULL DEFAULT 0,
            attempts        INTEGER NOT NULL DEFAULT 0,
            hints_used      INTEGER NOT NULL DEFAULT 0,
            points_earned   INTEGER NOT NULL DEFAULT 0,
            completed_at    TEXT,
            badges          TEXT    NOT NULL DEFAULT '[]',
            PRIMARY KEY (session_id, level_num)
        );
    """)
    conn.commit()


def seed_data(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM suspects")
    if cur.fetchone()[0] > 0:
        return  # already seeded

    # --- suspects (25 rows) ---
    # 5 in Docklands (Level 2 answer), top-3 motive_scores = [9,9,8] (Level 3)
    suspects = [
        # Docklands (5)
        (1,  "Alex Crane",       41, "Pawnbroker",      "Docklands",   9,  "Jordan Voss"),
        (2,  "Jordan Voss",      35, "Locksmith",       "Docklands",   9,  "Alex Crane"),
        (3,  "Taylor Ashford",   29, "Dock Worker",     "Docklands",   8,  None),
        (4,  "Shai Park",        44, "Smuggler",        "Docklands",   6,  "Yam Shade"),
        (5,  "Yuval Marchetti",  52, "Fence",           "Docklands",   5,  None),
        # Northside (5)
        (6,  "Yam Shade",        38, "Forger",          "Northside",   7,  "Shai Park"),
        (7,  "Avery Blayne",     27, "Pickpocket",      "Northside",   4,  None),
        (8,  "Jamie Holloway",   55, "Counterfeiter",   "Northside",   6,  "Alex Crane"),
        (9,  "Bar Ferrante",     33, "Thief",           "Northside",   3,  None),
        (10, "Eden Cross",       47, "Informant",       "Northside",   2,  "Avery Blayne"),
        # Old Quarter (5)
        (11, "Stav Wolfe",       31, "Arsonist",        "Old Quarter", 7,  "Taylor Ashford"),
        (12, "Cameron Blaine",   49, "Vandal",          "Old Quarter", 5,  None),
        (13, "Lior Vane",        23, "Con Artist",      "Old Quarter", 4,  "Jamie Holloway"),
        (14, "Ofek Favre",       36, "Smuggler",        "Old Quarter", 6,  "Stav Wolfe"),
        (15, "Aviv Monroe",      42, "Pickpocket",      "Old Quarter", 3,  None),
        # Riverside (5)
        (16, "Parker Aldric",    28, "Thief",           "Riverside",   5,  "Yuval Marchetti"),
        (17, "Amit Drax",        50, "Fence",           "Riverside",   4,  None),
        (18, "Adi Kestrel",      34, "Dock Worker",     "Riverside",   3,  "Parker Aldric"),
        (19, "Gal Callister",    26, "Locksmith",       "Riverside",   2,  None),
        (20, "Ariel Vance",      45, "Informant",       "Riverside",   1,  "Eden Cross"),
        # Midtown (5)
        (21, "Tal Harlow",       39, "Con Artist",      "Midtown",     4,  None),
        (22, "Yuval Solano",     32, "Forger",          "Midtown",     5,  "Yam Shade"),
        (23, "Noam Reston",      58, "Counterfeiter",   "Midtown",     3,  None),
        (24, "Ziv Moreau",       24, "Vandal",          "Midtown",     2,  "Yuval Solano"),
        (25, "Flynn Hartley",    46, "Arsonist",        "Midtown",     1,  None),
    ]
    conn.executemany(
        "INSERT INTO suspects VALUES (?,?,?,?,?,?,?)", suspects
    )

    # --- crimes (28 rows) ---
    # 10 in Docklands (Level 4 top group), others 3-6 each
    crimes = [
        # Docklands (10)
        (1,  "Theft",      "Docklands",   "2024-01-05", "Open",                 3),
        (2,  "Smuggling",  "Docklands",   "2024-01-12", "Under Investigation",  4),
        (3,  "Forgery",    "Docklands",   "2024-01-19", "Closed",               2),
        (4,  "Theft",      "Docklands",   "2024-02-03", "Open",                 3),
        (5,  "Vandalism",  "Docklands",   "2024-02-14", "Closed",               1),
        (6,  "Smuggling",  "Docklands",   "2024-02-28", "Under Investigation",  5),
        (7,  "Arson",      "Docklands",   "2024-03-07", "Open",                 5),
        (8,  "Theft",      "Docklands",   "2024-03-15", "Closed",               2),
        (9,  "Forgery",    "Docklands",   "2024-03-22", "Open",                 3),
        (10, "Smuggling",  "Docklands",   "2024-04-01", "Under Investigation",  4),
        # Northside (5)
        (11, "Forgery",    "Northside",   "2024-01-08", "Closed",               2),
        (12, "Theft",      "Northside",   "2024-02-20", "Open",                 3),
        (13, "Vandalism",  "Northside",   "2024-03-11", "Closed",               1),
        (14, "Arson",      "Northside",   "2024-03-29", "Open",                 5),
        (15, "Smuggling",  "Northside",   "2024-04-10", "Under Investigation",  4),
        # Old Quarter (5)
        (16, "Arson",      "Old Quarter", "2024-01-15", "Open",                 5),
        (17, "Theft",      "Old Quarter", "2024-02-07", "Closed",               2),
        (18, "Vandalism",  "Old Quarter", "2024-02-25", "Open",                 1),
        (19, "Forgery",    "Old Quarter", "2024-03-18", "Under Investigation",  3),
        (20, "Smuggling",  "Old Quarter", "2024-04-05", "Open",                 4),
        # Riverside (4)
        (21, "Theft",      "Riverside",   "2024-01-22", "Closed",               2),
        (22, "Vandalism",  "Riverside",   "2024-02-18", "Open",                 1),
        (23, "Arson",      "Riverside",   "2024-03-04", "Open",                 5),
        (24, "Forgery",    "Riverside",   "2024-04-15", "Under Investigation",  3),
        # Midtown (4)
        (25, "Vandalism",  "Midtown",     "2024-01-30", "Closed",               1),
        (26, "Theft",      "Midtown",     "2024-02-22", "Open",                 2),
        (27, "Smuggling",  "Midtown",     "2024-03-25", "Under Investigation",  4),
        (28, "Arson",      "Midtown",     "2024-04-20", "Open",                 5),
    ]
    conn.executemany(
        "INSERT INTO crimes VALUES (?,?,?,?,?,?)", crimes
    )

    # --- evidence (30 rows) ---
    # Exactly 4 rows with evidence_type = 'Physical' (Level 5 answer)
    # suspects 1,2,3,11 have Physical evidence
    evidence = [
        # Physical (4 rows) — suspects 1, 2, 3, 11
        (1,  2,  1,  "Physical",    8),
        (2,  6,  2,  "Physical",    7),
        (3,  7,  3,  "Physical",    9),
        (4,  16, 11, "Physical",    6),
        # Fingerprint (7 rows)
        (5,  1,  1,  "Fingerprint", 7),
        (6,  3,  2,  "Fingerprint", 5),
        (7,  4,  4,  "Fingerprint", 6),
        (8,  9,  3,  "Fingerprint", 4),
        (9,  11, 6,  "Fingerprint", 8),
        (10, 17, 7,  "Fingerprint", 3),
        (11, 21, 11, "Fingerprint", 6),
        # CCTV (7 rows)
        (12, 2,  1,  "CCTV",        9),
        (13, 5,  5,  "CCTV",        5),
        (14, 8,  2,  "CCTV",        7),
        (15, 12, 8,  "CCTV",        4),
        (16, 14, 6,  "CCTV",        6),
        (17, 19, 13, "CCTV",        5),
        (18, 22, 16, "CCTV",        3),
        # Witness (7 rows)
        (19, 1,  3,  "Witness",     6),
        (20, 6,  1,  "Witness",     4),
        (21, 10, 4,  "Witness",     7),
        (22, 13, 6,  "Witness",     5),
        (23, 18, 11, "Witness",     8),
        (24, 23, 14, "Witness",     3),
        (25, 25, 17, "Witness",     4),
        # Document (5 rows)
        (26, 3,  2,  "Document",    5),
        (27, 9,  1,  "Document",    6),
        (28, 15, 8,  "Document",    4),
        (29, 20, 6,  "Document",    7),
        (30, 24, 11, "Document",    5),
    ]
    conn.executemany(
        "INSERT INTO evidence VALUES (?,?,?,?,?)", evidence
    )

    conn.commit()


def safe_execute(conn: sqlite3.Connection, query: str):
    """Execute a SELECT-only query safely. Returns (DataFrame|None, error_str|None)."""
    stripped = query.strip()
    if not stripped:
        return None, "Enter a SQL query to run."
    if not stripped.lower().startswith("select"):
        return None, "Only SELECT queries are permitted, Detective."
    if FORBIDDEN.search(stripped):
        return None, "Query contains a forbidden keyword. Keep it to SELECT only."
    try:
        df = pd.read_sql_query(stripped, conn)
        return df, None
    except Exception as exc:
        return None, f"SQL Error: {exc}"


def get_table_info(conn: sqlite3.Connection) -> dict:
    """Return {table_name: [(col_name, col_type), ...]} for schema viewer."""
    tables = ["suspects", "crimes", "evidence"]
    info = {}
    for table in tables:
        cur = conn.execute(f"PRAGMA table_info({table})")
        info[table] = [(row["name"], row["type"]) for row in cur.fetchall()]
    return info
