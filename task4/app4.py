"""
app4.py — SQL Detective Agency: Learn SQL by solving crime cases.

Run:
    task2/.venv311/Scripts/streamlit run task4/app4.py
"""
import random as _random
import sys
import uuid
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from db_setup import get_db, safe_execute, get_table_info
from levels import LEVELS, LEVEL_MAP, ALL_COMPLETE_TEXT
from progress import (
    init_session,
    load_progress,
    increment_attempt,
    increment_hints,
    mark_complete,
    check_and_award_badges,
    get_badges,
    get_rank,
)
from styles import CSS
from ui_components import (
    render_avatar,
    render_sidebar,
    render_level_header,
    render_story,
    render_task,
    render_query_editor,
    render_result,
    render_hints,
    render_story_update,
    render_lock_panel,
    render_join_preview,
    render_sort_preview,
    render_where_preview,
    render_groupby_preview,
    render_sql_reference,
    render_challenge_visualization,
)

# ── Detective avatar messages ──────────────────────────────────────────────────

_LEVEL_MSG = {
    1: "Good work, {name}! Now we know all 25 suspects on file. The investigation begins!",
    2: "Sharp eyes, {name}! Five suspects in Docklands — the net is closing.",
    3: "Victor Crane tops the list, {name}! Keep your eyes on him.",
    4: "Ten crimes in Docklands is no coincidence, {name}. Something big is happening there.",
    5: "Physical evidence narrows it to four individuals, {name}. We're very close!",
    6: "Outstanding work, {name}! The mastermind has been unmasked. Case closed!",
}
_BADGE_MSG = {
    "first_blood": "Your first case closed, {name}! The Agency is proud.",
    "clean_sweep": "No hints needed? Impressive work, {name}!",
    "sharp_mind":  "First try! You have a sharp mind, {name}.",
    "persistent":  "Persistence pays off, {name}. A true bulldog never gives up!",
    "no_scaffold": "Wrote it from scratch? That's real detective-level SQL, {name}!",
    "five_star":   "All five cases closed, {name}! You've earned the Chief Inspector rank.",
    "mastermind":  "The mastermind unmasked! You're a legend in this Agency, {name}.",
}
_HINT_MSG = [
    "Every detective needs a clue sometimes, {name}. Study it carefully.",
    "One more hint, {name}. This should crack the case wide open.",
]
_CHIEF_ERROR_TEMPLATES = [
    "Hold on, {name} — your query hit a syntax snag. {issue} Fix it and try again.",
    "Easy, {name}. The database threw an error: {issue} Take another look.",
    "We've seen this before, {name}. {issue} Adjust your query and resubmit.",
]
_CHIEF_WRONG_TEMPLATES = [
    "Not quite, {name}. {issue} Study the case files again.",
    "Close but no cigar, {name}. {issue} You've got the right idea — refine it.",
    "The evidence doesn't add up, {name}. {issue} Try a different angle.",
    "I've seen sharper detectives stumble here, {name}. {issue}",
]


def _dname() -> str:
    n = st.session_state.get("detective_name", "") or ""
    return f"Detective {n}" if n else "Detective"


def _chief_says(issue: str, detective_name: str, is_error: bool) -> str:
    _random.seed(issue[:20])
    pool = _CHIEF_ERROR_TEMPLATES if is_error else _CHIEF_WRONG_TEMPLATES
    msg = _random.choice(pool).format(name=detective_name, issue=issue)
    _random.seed()
    return msg


# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SQL Detective Agency",
    page_icon="🕵️",
    layout="wide",
)
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

# ── DB init ────────────────────────────────────────────────────────────────────
conn = get_db()
table_info = get_table_info(conn)


# ── Session init ───────────────────────────────────────────────────────────────
def _init_session_state():
    if "session_id" not in st.session_state:
        st.session_state.session_id = uuid.uuid4().hex
        init_session(conn, st.session_state.session_id)

    sid = st.session_state.session_id
    progress = load_progress(conn, sid)

    if "completed_levels" not in st.session_state:
        st.session_state.completed_levels = {
            n for n, d in progress.items() if d["completed"]
        }
    if "points" not in st.session_state:
        st.session_state.points = sum(d["points_earned"] for d in progress.values())
    if "badges" not in st.session_state:
        st.session_state.badges = get_badges(conn, sid)
    if "streak" not in st.session_state:
        st.session_state.streak = 0
    if "prev_rank_pts" not in st.session_state:
        st.session_state.prev_rank_pts = st.session_state.points
    if "detective_name" not in st.session_state:
        st.session_state.detective_name = None
    if "avatar_message" not in st.session_state:
        st.session_state.avatar_message = ""

    for n in range(1, 7):
        for key in [f"query_input_{n}", f"last_error_{n}"]:
            if key not in st.session_state:
                st.session_state[key] = ""
        if f"last_result_{n}" not in st.session_state:
            st.session_state[f"last_result_{n}"] = None
        for key in [f"hint_level_{n}", f"attempts_{n}", f"reset_counter_{n}", f"add_row_count_{n}"]:
            if key not in st.session_state:
                st.session_state[key] = 0
        if f"is_correct_{n}" not in st.session_state:
            st.session_state[f"is_correct_{n}"] = None
        if f"diagnosis_{n}" not in st.session_state:
            st.session_state[f"diagnosis_{n}"] = None
        if f"pts_just_earned_{n}" not in st.session_state:
            st.session_state[f"pts_just_earned_{n}"] = None
        if f"new_badges_{n}" not in st.session_state:
            st.session_state[f"new_badges_{n}"] = []


_init_session_state()

# ── Sidebar ────────────────────────────────────────────────────────────────────
render_sidebar(
    {
        "completed_levels": st.session_state.completed_levels,
        "points":  st.session_state.points,
        "streak":  st.session_state.streak,
        "badges":  st.session_state.badges,
    },
    table_info,
)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <h1 style="text-align:center; color:#93c5fd; letter-spacing:2px;">
        🕵️ SQL Detective Agency
    </h1>
    <p style="text-align:center; color:#64748b; font-size:16px;">
        Learn SQL by solving real crime cases. Each challenge teaches a new skill.
    </p>
    """,
    unsafe_allow_html=True,
)

# ── Name collection (shown only on very first visit) ──────────────────────────
if st.session_state.detective_name is None:
    st.markdown(
        "<h2 style='text-align:center; color:#93c5fd;'>What's your name, Detective?</h2>",
        unsafe_allow_html=True,
    )
    _, col, _ = st.columns([1, 2, 1])
    name_input = col.text_input(
        "Your name (optional)",
        placeholder="e.g. Mike",
        label_visibility="collapsed",
    )
    c1, c2 = col.columns(2)
    if c1.button("▶ Start Investigation", type="primary", use_container_width=True):
        st.session_state.detective_name = name_input.strip()
        dn = _dname()
        st.session_state.avatar_message = (
            f"Welcome, {dn}! Your first case awaits. Study the suspects carefully."
        )
        st.rerun()
    if c2.button("Skip", use_container_width=True):
        st.session_state.detective_name = ""
        st.session_state.avatar_message = "Welcome, Detective! Your first case awaits."
        st.rerun()
    render_avatar(st.session_state.avatar_message)
    st.stop()

# SQL reference always at the top
render_sql_reference()

# ── Tab construction ───────────────────────────────────────────────────────────
completed = st.session_state.completed_levels
bonus_unlocked = {1, 2, 3, 4, 5}.issubset(completed)

tab_labels = [f"Challenge {i}" for i in range(1, 6)] + (["🌟 Bonus"] if bonus_unlocked else [])
tabs = st.tabs(tab_labels)


def _is_unlocked(level_num: int) -> bool:
    if level_num == 1:
        return True
    if level_num == 6:
        return bonus_unlocked
    return (level_num - 1) in completed


def _render_level(tab, level_num: int) -> None:
    lvl = LEVEL_MAP[level_num]
    sid = st.session_state.session_id
    is_completed = level_num in completed

    with tab:
        if not _is_unlocked(level_num):
            render_lock_panel(level_num)
            return

        render_level_header(lvl, is_completed)
        render_story(lvl["story"])
        render_task(lvl["task"])

        # Static visual aids (always shown — helps understand the task)
        if level_num == 2:
            render_where_preview(conn)
        elif level_num == 3:
            render_sort_preview(conn)
        elif level_num == 4:
            render_groupby_preview(conn)
        elif level_num == 5:
            render_join_preview(conn)

        # Per-challenge data visualization — revealed only after solving
        if is_completed:
            render_challenge_visualization(level_num, conn)

        st.markdown("---")

        # Query editor
        run_clicked, hint_clicked, reset_clicked, add_row_clicked = render_query_editor(
            level_num, lvl["correct_query_lines"]
        )

        # ── Handle Add Row ─────────────────────────────────────────────────────
        if add_row_clicked:
            current = st.session_state.get(f"add_row_count_{level_num}", 0)
            max_rows = len(lvl["correct_query_lines"])
            if current < max_rows:
                st.session_state[f"add_row_count_{level_num}"] = current + 1
            st.rerun()

        # ── Handle Reset ───────────────────────────────────────────────────────
        if reset_clicked:
            st.session_state[f"reset_counter_{level_num}"] += 1
            st.session_state[f"add_row_count_{level_num}"] = 0
            st.session_state[f"last_result_{level_num}"] = None
            st.session_state[f"last_error_{level_num}"] = ""
            st.session_state[f"is_correct_{level_num}"] = None
            st.session_state[f"diagnosis_{level_num}"] = None
            st.session_state[f"pts_just_earned_{level_num}"] = None
            st.session_state[f"new_badges_{level_num}"] = []
            st.rerun()

        # ── Handle Hint ────────────────────────────────────────────────────────
        if hint_clicked:
            current_hint = st.session_state.get(f"hint_level_{level_num}", 0)
            if current_hint < 2:
                new_hint = current_hint + 1
                st.session_state[f"hint_level_{level_num}"] = new_hint
                increment_hints(conn, sid, level_num)
                if new_hint == 1:
                    st.session_state.streak = 0
                hint_idx = min(new_hint - 1, 1)
                st.session_state.avatar_message = _HINT_MSG[hint_idx].format(name=_dname())
            st.rerun()

        # ── Handle Run ─────────────────────────────────────────────────────────
        if run_clicked:
            query = st.session_state.get(f"query_input_{level_num}", "").strip()
            df, error = safe_execute(conn, query)
            st.session_state[f"last_result_{level_num}"] = df
            st.session_state[f"last_error_{level_num}"] = error or ""

            if df is not None and error is None:
                new_attempt_count = increment_attempt(conn, sid, level_num)
                st.session_state[f"attempts_{level_num}"] = new_attempt_count

                is_correct = lvl["check_fn"](df)
                st.session_state[f"is_correct_{level_num}"] = is_correct

                if is_correct and level_num not in completed:
                    hints_used = st.session_state.get(f"hint_level_{level_num}", 0)
                    add_row_used = st.session_state.get(f"add_row_count_{level_num}", 0)
                    pts = mark_complete(conn, sid, level_num, new_attempt_count, hints_used)
                    st.session_state[f"pts_just_earned_{level_num}"] = pts
                    st.session_state.points += pts
                    st.session_state.completed_levels.add(level_num)

                    if new_attempt_count == 1 and hints_used == 0 and add_row_used == 0:
                        st.session_state.streak += 1
                    else:
                        st.session_state.streak = 0

                    new_badges = check_and_award_badges(
                        conn, sid, level_num,
                        new_attempt_count, hints_used,
                        st.session_state.completed_levels,
                        add_row_used=add_row_used,
                    )
                    st.session_state[f"new_badges_{level_num}"] = new_badges
                    st.session_state.badges = get_badges(conn, sid)

                    old_rank, _ = get_rank(st.session_state.prev_rank_pts)
                    new_rank, _ = get_rank(st.session_state.points)
                    if new_rank != old_rank:
                        st.balloons()
                    st.session_state.prev_rank_pts = st.session_state.points

                    # Avatar: badge message takes priority over level message
                    dn = _dname()
                    if new_badges:
                        st.session_state.avatar_message = _BADGE_MSG.get(
                            new_badges[0], _LEVEL_MSG[level_num]
                        ).format(name=dn)
                    else:
                        st.session_state.avatar_message = _LEVEL_MSG[level_num].format(name=dn)

                elif is_correct and level_num in completed:
                    st.session_state[f"pts_just_earned_{level_num}"] = None
                    st.session_state[f"new_badges_{level_num}"] = []

                else:
                    # Wrong answer — auto-show hint 1 if not already shown
                    st.session_state[f"diagnosis_{level_num}"] = lvl["diagnose_fn"](df, query)
                    st.session_state[f"pts_just_earned_{level_num}"] = None
                    st.session_state[f"new_badges_{level_num}"] = []
                    st.session_state.streak = 0
                    current_hint = st.session_state.get(f"hint_level_{level_num}", 0)
                    if current_hint == 0:
                        st.session_state[f"hint_level_{level_num}"] = 1
                        increment_hints(conn, sid, level_num)
                    # Avatar: explain the wrong answer in detective voice
                    diag = st.session_state[f"diagnosis_{level_num}"]
                    st.session_state.avatar_message = _chief_says(diag, _dname(), is_error=False)
            else:
                # SQL error — auto-show hint 1 if not already shown
                st.session_state[f"is_correct_{level_num}"] = None
                st.session_state[f"diagnosis_{level_num}"] = None
                current_hint = st.session_state.get(f"hint_level_{level_num}", 0)
                if current_hint == 0:
                    st.session_state[f"hint_level_{level_num}"] = 1
                    increment_hints(conn, sid, level_num)
                # Avatar: explain the SQL error in detective voice
                st.session_state.avatar_message = _chief_says(error or "", _dname(), is_error=True)

            st.rerun()

        # ── Render results ─────────────────────────────────────────────────────
        df_cached = st.session_state.get(f"last_result_{level_num}")
        error_cached = st.session_state.get(f"last_error_{level_num}") or None
        is_correct_cached = st.session_state.get(f"is_correct_{level_num}")
        if level_num in completed and df_cached is not None and lvl["check_fn"](df_cached):
            is_correct_cached = True
        diagnosis_cached = st.session_state.get(f"diagnosis_{level_num}")
        pts_cached = st.session_state.get(f"pts_just_earned_{level_num}")
        badges_cached = st.session_state.get(f"new_badges_{level_num}", [])

        render_result(
            level_num, df_cached, error_cached,
            is_correct_cached, diagnosis_cached,
            pts_cached, badges_cached,
        )

        render_hints(level_num, lvl)
        render_story_update(level_num, completed, ALL_COMPLETE_TEXT)


# ── Render all tabs ────────────────────────────────────────────────────────────
for i, tab in enumerate(tabs):
    if i < 5:
        _render_level(tab, i + 1)
    else:
        _render_level(tab, 6)

# ── Floating detective avatar (always rendered at page bottom) ─────────────────
render_avatar(st.session_state.get("avatar_message", ""))
