"""
progress.py — Read/write progress and badges to/from detective_log table.
"""
import json
import sqlite3
from datetime import datetime, timezone


BADGE_META = {
    "first_blood": {"name": "First Case Closed",    "icon": "🔍", "desc": "Solve your first challenge."},
    "clean_sweep": {"name": "No Hints Needed",       "icon": "🧠", "desc": "Solve any challenge without using hints."},
    "sharp_mind":  {"name": "First Try Detective",   "icon": "⚡", "desc": "Solve any challenge on the very first attempt."},
    "persistent":  {"name": "Bulldog",               "icon": "🐶", "desc": "Use both hints but still crack the challenge."},
    "no_scaffold": {"name": "No Scaffolding",        "icon": "🧩", "desc": "Solve a challenge without using Add Row."},
    "five_star":   {"name": "Case Closed: All Files","icon": "🌟", "desc": "Complete all 5 main challenges."},
    "mastermind":  {"name": "Mastermind Hunter",     "icon": "👑", "desc": "Solve the secret bonus challenge."},
}

RANK_THRESHOLDS = [
    (80, "Master Detective",  "🏆"),
    (65, "Chief Inspector",   "🎖️"),
    (45, "Senior Detective",  "🔱"),
    (20, "Junior Detective",  "🔎"),
    (0,  "Rookie Constable",  "🚔"),
]

POINTS_FOR_ATTEMPT = {1: 15, 2: 10}  # 3+ → 5


def get_rank(points: int) -> tuple[str, str]:
    """Return (rank_title, rank_icon) for the given point total."""
    for threshold, title, icon in RANK_THRESHOLDS:
        if points >= threshold:
            return title, icon
    return "Rookie Constable", "🚔"


def points_for(attempts: int) -> int:
    return POINTS_FOR_ATTEMPT.get(attempts, 5)


def init_session(conn: sqlite3.Connection, session_id: str) -> None:
    """Ensure all 6 level rows exist for this session."""
    for level_num in range(1, 7):
        conn.execute(
            """
            INSERT OR IGNORE INTO detective_log
                (session_id, level_num, completed, attempts, hints_used, points_earned, badges)
            VALUES (?, ?, 0, 0, 0, 0, '[]')
            """,
            (session_id, level_num),
        )
    conn.commit()


def load_progress(conn: sqlite3.Connection, session_id: str) -> dict:
    cur = conn.execute(
        "SELECT * FROM detective_log WHERE session_id = ? ORDER BY level_num",
        (session_id,),
    )
    rows = cur.fetchall()
    result = {}
    for row in rows:
        result[row["level_num"]] = {
            "completed":     bool(row["completed"]),
            "attempts":      row["attempts"],
            "hints_used":    row["hints_used"],
            "points_earned": row["points_earned"],
            "badges":        json.loads(row["badges"] or "[]"),
        }
    return result


def increment_attempt(conn: sqlite3.Connection, session_id: str, level_num: int) -> int:
    conn.execute(
        "UPDATE detective_log SET attempts = attempts + 1 WHERE session_id = ? AND level_num = ?",
        (session_id, level_num),
    )
    conn.commit()
    cur = conn.execute(
        "SELECT attempts FROM detective_log WHERE session_id = ? AND level_num = ?",
        (session_id, level_num),
    )
    return cur.fetchone()["attempts"]


def increment_hints(conn: sqlite3.Connection, session_id: str, level_num: int) -> int:
    conn.execute(
        "UPDATE detective_log SET hints_used = hints_used + 1 WHERE session_id = ? AND level_num = ?",
        (session_id, level_num),
    )
    conn.commit()
    cur = conn.execute(
        "SELECT hints_used FROM detective_log WHERE session_id = ? AND level_num = ?",
        (session_id, level_num),
    )
    return cur.fetchone()["hints_used"]


def mark_complete(
    conn: sqlite3.Connection,
    session_id: str,
    level_num: int,
    attempts: int,
    hints_used: int,
) -> int:
    cur = conn.execute(
        "SELECT completed FROM detective_log WHERE session_id = ? AND level_num = ?",
        (session_id, level_num),
    )
    row = cur.fetchone()
    if row and row["completed"]:
        cur2 = conn.execute(
            "SELECT points_earned FROM detective_log WHERE session_id = ? AND level_num = ?",
            (session_id, level_num),
        )
        return cur2.fetchone()["points_earned"]

    pts = points_for(attempts)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        UPDATE detective_log
        SET completed = 1, attempts = ?, hints_used = ?, points_earned = ?, completed_at = ?
        WHERE session_id = ? AND level_num = ?
        """,
        (attempts, hints_used, pts, now, session_id, level_num),
    )
    conn.commit()
    return pts


def award_badge(conn: sqlite3.Connection, session_id: str, badge_id: str) -> bool:
    """Award a badge. Returns True if newly awarded, False if already had it."""
    cur = conn.execute(
        "SELECT badges FROM detective_log WHERE session_id = ? AND level_num = 1",
        (session_id,),
    )
    row = cur.fetchone()
    if not row:
        return False
    badges = json.loads(row["badges"] or "[]")
    if badge_id in badges:
        return False
    badges.append(badge_id)
    conn.execute(
        "UPDATE detective_log SET badges = ? WHERE session_id = ? AND level_num = 1",
        (json.dumps(badges), session_id),
    )
    conn.commit()
    return True


def get_badges(conn: sqlite3.Connection, session_id: str) -> list:
    cur = conn.execute(
        "SELECT badges FROM detective_log WHERE session_id = ? AND level_num = 1",
        (session_id,),
    )
    row = cur.fetchone()
    if not row:
        return []
    return json.loads(row["badges"] or "[]")


def check_and_award_badges(
    conn: sqlite3.Connection,
    session_id: str,
    level_num: int,
    attempts: int,
    hints_used: int,
    completed_levels: set,
    add_row_used: int = 0,
) -> list:
    """Check and award badges after solving a level. Returns list of new badge IDs."""
    existing = set(get_badges(conn, session_id))
    new_badges = []

    def maybe_award(bid):
        if bid not in existing:
            if award_badge(conn, session_id, bid):
                new_badges.append(bid)

    if level_num == 1:
        maybe_award("first_blood")
    if hints_used == 0:
        maybe_award("clean_sweep")
    if attempts == 1:
        maybe_award("sharp_mind")
    if hints_used >= 2 and attempts >= 2:
        maybe_award("persistent")
    if add_row_used == 0:
        maybe_award("no_scaffold")
    if {1, 2, 3, 4, 5}.issubset(completed_levels | {level_num}):
        maybe_award("five_star")
    if level_num == 6:
        maybe_award("mastermind")

    return new_badges
