"""
ui_components.py — Reusable UI widgets for the SQL Detective Agency app.
"""
import base64
import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from levels import LEVELS, LEVEL_MAP
from progress import BADGE_META, get_rank


# ── Markdown → HTML helper ─────────────────────────────────────────────────────

def _md(text: str) -> str:
    """Convert **bold** and `code` markdown to HTML tags for use inside HTML blocks."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text


# ── SQL Reference panel ────────────────────────────────────────────────────────

_ROW_A = "background:#060d1a"
_ROW_B = "background:#0c1627"
_TD    = "padding:6px 14px; border-bottom:1px solid #1e293b;"

SQL_REFERENCE = f"""
<div style="background:#060d1a; border:1px solid #1e293b; border-radius:8px; overflow:hidden;">
<table style="width:100%; border-collapse:collapse; font-size:13px; font-family:'Courier New',monospace;">
<tr style="background:#0a1628; border-bottom:2px solid #3b82f6;">
  <th style="text-align:left; {_TD} color:#93c5fd; width:110px;">Clause</th>
  <th style="text-align:left; {_TD} color:#93c5fd;">Syntax</th>
  <th style="text-align:left; {_TD} color:#64748b;">Purpose</th>
</tr>
<tr style="{_ROW_A}"><td style="{_TD} color:#a5f3fc;">SELECT</td>
    <td style="{_TD} color:#e2e8f0;">SELECT col1, col2 &nbsp;<em style="color:#475569;">or</em>&nbsp; SELECT *</td>
    <td style="{_TD} color:#64748b;">Choose columns (* = all)</td></tr>
<tr style="{_ROW_B}"><td style="{_TD} color:#a5f3fc;">FROM</td>
    <td style="{_TD} color:#e2e8f0;">FROM table_name</td>
    <td style="{_TD} color:#64748b;">Which table to query</td></tr>
<tr style="{_ROW_A}"><td style="{_TD} color:#a5f3fc;">JOIN … ON</td>
    <td style="{_TD} color:#e2e8f0;">JOIN table2 ON t1.col1 = t2.col2</td>
    <td style="{_TD} color:#64748b;">Link two tables by shared column</td></tr>
<tr style="{_ROW_B}"><td style="{_TD} color:#a5f3fc;">WHERE</td>
    <td style="{_TD} color:#e2e8f0;">WHERE column_name = <span style="color:#86efac;">'value'</span> &nbsp;<em style="color:#475569;">or</em>&nbsp; WHERE n &gt; 5</td>
    <td style="{_TD} color:#64748b;">Filter rows (text needs quotes)</td></tr>
<tr style="{_ROW_A}"><td style="{_TD} color:#a5f3fc;">GROUP BY</td>
    <td style="{_TD} color:#e2e8f0;">GROUP BY column_name</td>
    <td style="{_TD} color:#64748b;">Group rows, use with COUNT / SUM / AVG</td></tr>
<tr style="{_ROW_B}"><td style="{_TD} color:#a5f3fc;">COUNT</td>
    <td style="{_TD} color:#e2e8f0;">COUNT(*) AS alias_name</td>
    <td style="{_TD} color:#64748b;">Count rows in each group</td></tr>
<tr style="{_ROW_A}"><td style="{_TD} color:#a5f3fc;">HAVING</td>
    <td style="{_TD} color:#e2e8f0;">HAVING COUNT(*) &gt; 1</td>
    <td style="{_TD} color:#64748b;">Filter groups after GROUP BY</td></tr>
<tr style="{_ROW_B}"><td style="{_TD} color:#a5f3fc;">ORDER BY</td>
    <td style="{_TD} color:#e2e8f0;">ORDER BY column_name <span style="color:#fbbf24;">DESC</span> &nbsp;<em style="color:#475569;">or</em>&nbsp; ORDER BY column_name <span style="color:#fbbf24;">ASC</span></td>
    <td style="{_TD} color:#64748b;">Sort rows (DESC = largest first)</td></tr>
<tr style="{_ROW_A}"><td style="{_TD} color:#a5f3fc; border-bottom:none;">LIMIT</td>
    <td style="{_TD} color:#e2e8f0; border-bottom:none;">LIMIT number_of_rows</td>
    <td style="{_TD} color:#64748b; border-bottom:none;">Cap the number of rows returned</td></tr>
</table>
<p style="color:#334155; font-size:11px; margin:6px 14px; font-family:'Courier New',monospace;">
  ↳ Full order: SELECT &nbsp;·&nbsp; FROM &nbsp;·&nbsp; JOIN…ON &nbsp;·&nbsp; WHERE &nbsp;·&nbsp; GROUP BY &nbsp;·&nbsp; HAVING &nbsp;·&nbsp; ORDER BY &nbsp;·&nbsp; LIMIT
</p>
</div>
"""


def render_sql_reference() -> None:
    with st.expander("📖 SQL Quick Reference", expanded=True):
        st.markdown(SQL_REFERENCE, unsafe_allow_html=True)


# ── Schema viewer ─────────────────────────────────────────────────────────────

def render_schema_viewer(table_info: dict) -> None:
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📂 Database Schema**")
    for table_name, columns in table_info.items():
        with st.sidebar.expander(f"`{table_name}` ({len(columns)} cols)"):
            df = pd.DataFrame(columns, columns=["Column", "Type"])
            st.dataframe(df, hide_index=True, use_container_width=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────

def render_sidebar(session: dict, table_info: dict) -> None:
    completed = session.get("completed_levels", set())
    points = session.get("points", 0)
    streak = session.get("streak", 0)
    badges = session.get("badges", [])

    rank_title, rank_icon = get_rank(points)

    st.sidebar.markdown(
        """
        <div style="text-align:center; padding:8px 0 4px 0;">
            <div style="font-size:48px;">🕵️</div>
            <div style="font-size:13px; color:#94a3b8; letter-spacing:2px;">
                SQL DETECTIVE AGENCY
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        f"""
        <div class="rank-badge">
            <div style="font-size:22px;">{rank_icon}</div>
            <div style="font-weight:bold; color:#93c5fd; font-size:15px;">{rank_title}</div>
            <div style="color:#64748b; font-size:12px;">{points} pts</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if streak >= 3:
        st.sidebar.markdown(
            f'<div class="streak-bar">🔥 On Fire! Streak: {streak}</div>',
            unsafe_allow_html=True,
        )
    elif streak > 0:
        st.sidebar.markdown(f"🔥 Streak: **{streak}**")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**📋 Challenge Progress**")
    main_levels = [l for l in LEVELS if l["num"] <= 5]
    for lvl in main_levels:
        if lvl["num"] in completed:
            icon = "✅"
        elif lvl["num"] == 1 or (lvl["num"] - 1) in completed:
            icon = "🔓"
        else:
            icon = "🔒"
        st.sidebar.markdown(f"{icon} **Challenge {lvl['num']}:** {lvl['title']}")

    bonus = LEVEL_MAP[6]
    if {1, 2, 3, 4, 5}.issubset(completed):
        b_icon = "✅" if 6 in completed else "🔓"
        st.sidebar.markdown(f"{b_icon} **Bonus:** {bonus['title']}")
    else:
        st.sidebar.markdown(f"🔐 **Bonus:** {bonus['title']} *(unlock all 5)*")

    if badges:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**🏅 Badges**")
        badge_html = '<div class="badge-shelf">'
        for bid in badges:
            meta = BADGE_META.get(bid, {})
            badge_html += (
                f'<span class="badge-item earned" title="{meta.get("desc","")}">'
                f'{meta.get("icon","🏅")} {meta.get("name", bid)}</span>'
            )
        badge_html += "</div>"
        st.sidebar.markdown(badge_html, unsafe_allow_html=True)

    render_schema_viewer(table_info)


# ── Level header ───────────────────────────────────────────────────────────────

def render_level_header(lvl: dict, is_completed: bool) -> None:
    solved_badge = (
        '<span class="case-badge">✅ SOLVED</span>' if is_completed else ""
    )
    num = lvl["num"]
    label = "Bonus" if num == 6 else f"Challenge {num}"
    st.markdown(
        f"## 🔎 {label}: {lvl['title']} {solved_badge}",
        unsafe_allow_html=True,
    )
    st.markdown(f"*SQL Concept: **{lvl['concept']}***")


# ── Story and task boxes ───────────────────────────────────────────────────────

def render_story(text: str) -> None:
    st.markdown(
        f'<div class="story-box">📖 {_md(text)}</div>',
        unsafe_allow_html=True,
    )


def render_task(text: str) -> None:
    st.markdown(
        f'<div class="task-box">🎯 <strong>Your Mission:</strong><br>{_md(text)}</div>',
        unsafe_allow_html=True,
    )


# ── Query editor with Add Row ──────────────────────────────────────────────────

def render_query_editor(level_num: int, correct_query_lines: list) -> tuple:
    """
    Renders the SQL text area and control buttons.
    Returns (run_clicked, hint_clicked, reset_clicked, add_row_clicked).

    Uses reset_counter in the widget key so incrementing it forces a fresh
    empty text area without triggering the "cannot modify widget state" error.
    """
    reset_counter = st.session_state.get(f"reset_counter_{level_num}", 0)
    widget_key = f"query_input_{level_num}_{reset_counter}"
    # Sync stable alias before widget renders
    if widget_key not in st.session_state:
        st.session_state[widget_key] = st.session_state.get(f"query_input_{level_num}", "")

    st.text_area(
        "✏️ Write your SQL query:",
        key=widget_key,
        height=120,
        placeholder="-- Type your SELECT query here\nSELECT ...",
    )
    # Keep stable alias in sync after widget renders
    st.session_state[f"query_input_{level_num}"] = st.session_state.get(widget_key, "")

    # Add Row: show accumulated scaffold lines
    add_row_count = st.session_state.get(f"add_row_count_{level_num}", 0)
    if add_row_count > 0:
        revealed = correct_query_lines[:add_row_count]
        st.code("\n".join(revealed), language="sql")
        st.caption(
            f"📝 Scaffold: {add_row_count} / {len(correct_query_lines)} lines revealed"
            + (" — complete!" if add_row_count == len(correct_query_lines) else "")
        )

    col1, col2, col3, col4 = st.columns([3, 2, 1, 3])
    with col1:
        run = st.button("▶ Run Query", key=f"run_{level_num}", type="primary")
    with col2:
        hint = st.button("💡 Hint", key=f"hint_{level_num}")
    with col3:
        reset = st.button("🔄", key=f"reset_{level_num}", help="Reset query")
    with col4:
        max_rows = len(correct_query_lines)
        rows_left = max_rows - add_row_count
        add_row_label = (
            f"📝 Add Row ({add_row_count}/{max_rows})" if add_row_count > 0
            else "📝 Add Row"
        )
        add_row = st.button(
            add_row_label,
            key=f"add_row_{level_num}",
            disabled=(rows_left == 0),
            help=f"{rows_left} line(s) remaining — reveals the next line of the correct query",
        )

    return run, hint, reset, add_row


# ── Result display ─────────────────────────────────────────────────────────────

def render_result(
    level_num: int,
    df,
    error,
    is_correct,
    diagnosis,
    points_just_earned,
    new_badges: list,
) -> None:
    if error:
        st.markdown(
            f'<div class="error-banner">⚠️ {error}</div>',
            unsafe_allow_html=True,
        )
        return

    if df is not None:
        st.markdown(f"**Results** — {len(df)} row(s) returned")
        _render_highlighted_df(level_num, df)

    if is_correct is True:
        pts_text = f"+{points_just_earned} pts" if points_just_earned else ""
        st.markdown(
            f'<div class="solved-banner">✅ CHALLENGE SOLVED! {pts_text}</div>',
            unsafe_allow_html=True,
        )
        if new_badges:
            for bid in new_badges:
                meta = BADGE_META.get(bid, {})
                st.toast(f"🏅 Badge Unlocked: {meta.get('name', bid)}!")
            # Clear so they don't fire again on subsequent reruns (e.g. Add Row clicks)
            st.session_state[f"new_badges_{level_num}"] = []
    elif is_correct is False and diagnosis:
        st.markdown(
            f'<div class="error-banner">❌ {diagnosis}</div>',
            unsafe_allow_html=True,
        )


def _render_highlighted_df(level_num: int, df: pd.DataFrame) -> None:
    if level_num == 2 and "district" in df.columns:
        def _highlight(row):
            if row.get("district") == "Docklands":
                return ["background-color: #3d3000; color: #fef3c7"] * len(row)
            return [""] * len(row)
        st.dataframe(df.style.apply(_highlight, axis=1), use_container_width=True)
    elif level_num == 5:
        st.caption("🔗 JOIN result — suspects linked to evidence")
        st.dataframe(df, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)


# ── Visual JOIN preview ────────────────────────────────────────────────────────

def render_join_preview(conn: sqlite3.Connection) -> None:
    with st.expander("📊 Visual: How JOIN works", expanded=True):
        c1, c2, c3 = st.columns([5, 1, 5])
        with c1:
            st.caption("**suspects** (first 5 rows)")
            df_s = pd.read_sql_query(
                "SELECT suspect_id, name, district FROM suspects LIMIT 5", conn
            )
            st.dataframe(df_s, hide_index=True, use_container_width=True)
        with c2:
            st.markdown("<br><br>➡️", unsafe_allow_html=True)
        with c3:
            st.caption("**evidence** (first 5 rows)")
            df_e = pd.read_sql_query(
                "SELECT evidence_id, suspect_id, evidence_type FROM evidence LIMIT 5", conn
            )
            st.dataframe(df_e, hide_index=True, use_container_width=True)
        st.markdown(
            "The shared column is `suspect_id`. "
            "JOIN matches each evidence row to the suspect with the same ID."
        )


# ── ORDER BY comparison preview ────────────────────────────────────────────────

def render_sort_preview(conn: sqlite3.Connection) -> None:
    with st.expander("📊 Visual: How ORDER BY works", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.caption("**Unsorted** (first 5 rows)")
            df_u = pd.read_sql_query(
                "SELECT name, motive_score FROM suspects ORDER BY suspect_id % 7 LIMIT 5", conn
            )
            st.dataframe(df_u, hide_index=True, use_container_width=True)
        with c2:
            st.caption("**After ORDER BY motive_score DESC LIMIT 5**")
            df_s = pd.read_sql_query(
                "SELECT name, motive_score FROM suspects ORDER BY motive_score DESC LIMIT 5",
                conn,
            )
            st.dataframe(df_s, hide_index=True, use_container_width=True)
        st.markdown("Notice how the highest scores now appear at the top.")


def render_where_preview(conn: sqlite3.Connection) -> None:
    with st.expander("📊 Visual: How WHERE works", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.caption("**All rows** (no filter)")
            df_all = pd.read_sql_query(
                "SELECT name, district FROM suspects LIMIT 8", conn
            )
            st.dataframe(df_all, hide_index=True, use_container_width=True)
        with c2:
            st.caption("**After WHERE district = 'Docklands'**")
            df_f = pd.read_sql_query(
                "SELECT name, district FROM suspects WHERE district = 'Docklands'", conn
            )
            st.dataframe(df_f, hide_index=True, use_container_width=True)
        st.markdown("WHERE keeps only the rows where the condition is true — all others are discarded.")


def render_groupby_preview(conn: sqlite3.Connection) -> None:
    with st.expander("📊 Visual: How GROUP BY works", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.caption("**crimes table** (raw rows, first 8)")
            df_raw = pd.read_sql_query(
                "SELECT crime_id, district FROM crimes LIMIT 8", conn
            )
            st.dataframe(df_raw, hide_index=True, use_container_width=True)
        with c2:
            st.caption("**After GROUP BY district + COUNT(*)**")
            df_g = pd.read_sql_query(
                "SELECT district, COUNT(*) AS crime_count FROM crimes GROUP BY district ORDER BY crime_count DESC",
                conn,
            )
            st.dataframe(df_g, hide_index=True, use_container_width=True)
        st.markdown(
            "GROUP BY collapses all rows sharing the same `district` into one row, "
            "and COUNT(*) tells you how many rows were merged."
        )


# ── Per-challenge visualizations ───────────────────────────────────────────────

_DARK = "#0f172a"
_GRID = "#1e293b"
_TEXT = "#94a3b8"

_DISTRICT_COLORS = {
    "Docklands":   "#ef4444",
    "Old Quarter": "#f59e0b",
    "Northside":   "#3b82f6",
    "Riverside":   "#10b981",
    "Midtown":     "#8b5cf6",
}

# Fake city grid positions for district map
_DISTRICT_XY = {
    "Northside":   (2.5, 4.2),
    "Old Quarter": (3.2, 3.0),
    "Docklands":   (1.3, 2.5),
    "Riverside":   (4.5, 2.0),
    "Midtown":     (3.0, 1.2),
}


_FACES_DIR = Path(__file__).parent / "faces"


def _get_face_files() -> list:
    """Return exactly 25 face image paths sorted numerically, any filename format."""
    if not _FACES_DIR.exists():
        return []
    files = [
        f for f in _FACES_DIR.iterdir()
        if f.suffix.lower() in (".jpg", ".jpeg", ".png") and f.is_file()
    ]
    # Sort numerically by stem if possible (0.jpg, 1.jpg, …), else lexically
    def _sort_key(p):
        try:
            return int(p.stem)
        except ValueError:
            return p.stem
    return sorted(files, key=_sort_key)[:25]


@st.cache_data(show_spinner=False)
def _load_face_b64_list() -> list:
    """Read and base64-encode all 25 face images once; cached for the app lifetime."""
    face_files = _get_face_files()
    return [
        base64.b64encode(p.read_bytes()).decode()
        for p in face_files
    ]


def render_challenge_visualization(level_num: int, conn: sqlite3.Connection) -> None:
    """Render a relevant plotly visualization for the given challenge."""
    label = "Bonus" if level_num == 6 else f"Challenge {level_num}"
    with st.expander(f"📊 Investigation Data — {label}", expanded=True):
        if level_num == 1:
            face_files = _get_face_files()
            if len(face_files) >= 25:
                _viz_suspect_faces(conn, face_files)
            else:
                _viz_occupations(conn)
        elif level_num == 2:
            _viz_suspects_by_district(conn)
        elif level_num == 3:
            _viz_motive_leaderboard(conn)
        elif level_num == 4:
            _viz_crime_city_map(conn)
        elif level_num == 5:
            _viz_evidence_heatmap(conn)
        elif level_num == 6:
            _viz_repeat_offenders(conn)


def _fig_layout(fig, title: str, height: int = 350) -> None:
    fig.update_layout(
        title=dict(text=title, font=dict(color="#93c5fd", size=14)),
        plot_bgcolor=_DARK,
        paper_bgcolor=_DARK,
        font=dict(color=_TEXT),
        margin=dict(l=10, r=10, t=40, b=10),
        height=height,
    )


def _viz_suspect_faces(conn: sqlite3.Connection, face_files: list) -> None:
    """Police dossier: AI face photo + name + district badge for all 25 suspects."""
    df = pd.read_sql_query(
        "SELECT name, district, occupation, motive_score FROM suspects ORDER BY suspect_id",
        conn,
    )
    face_b64 = _load_face_b64_list()

    st.markdown(
        """
        <div style="background:#060d1a; border:1px solid #1e293b; border-radius:8px;
                    padding:10px 16px 4px 16px; margin-bottom:12px;">
          <span style="color:#93c5fd; font-family:'Courier New'; font-size:13px; letter-spacing:2px;">
            🔦 POLICE DOSSIER — ALL 25 SUSPECTS — CLASSIFIED (AI GENERATED FACES)
          </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    COLS = 5
    for row_start in range(0, 25, COLS):
        cols = st.columns(COLS)
        for col_idx, suspect_i in enumerate(range(row_start, min(row_start + COLS, 25))):
            suspect = df.iloc[suspect_i]
            district  = suspect["district"]
            score     = suspect["motive_score"]
            color     = _DISTRICT_COLORS.get(district, "#475569")
            badge_col = "#ef4444" if score >= 8 else "#f59e0b" if score >= 5 else "#22c55e"

            img_b64 = face_b64[suspect_i] if suspect_i < len(face_b64) else ""

            with cols[col_idx]:
                st.markdown(
                    f"""
                    <div style="background:#0a0f1e; border:2px solid {color};
                                border-radius:8px; padding:6px; text-align:center;
                                margin-bottom:4px;">
                      <img src="data:image/jpeg;base64,{img_b64}"
                           style="width:100%; border-radius:4px; display:block;" />
                      <div style="font-family:'Courier New'; font-size:11px;
                                  color:white; margin-top:4px; font-weight:bold;
                                  white-space:nowrap; overflow:hidden;
                                  text-overflow:ellipsis;">
                        {suspect['name']}
                      </div>
                      <div style="font-size:10px; color:{color}; margin-top:1px;">
                        {district}
                      </div>
                      <div style="font-size:10px; color:#64748b; margin-top:1px;">
                        {suspect['occupation']}
                      </div>
                      <div style="margin-top:4px;">
                        <span style="background:{badge_col}; color:white;
                                     font-size:9px; border-radius:8px;
                                     padding:1px 6px; font-family:'Courier New';">
                          MOTIVE {score}/10
                        </span>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Legend
    legend_html = " &nbsp;·&nbsp; ".join(
        f'<span style="color:{c};">■</span> {d}' for d, c in _DISTRICT_COLORS.items()
    )
    st.markdown(
        f'<p style="font-size:11px; color:#475569; font-family:Courier New; margin-top:6px;">'
        f'Border color = district &nbsp;|&nbsp; {legend_html}</p>',
        unsafe_allow_html=True,
    )


def _viz_occupations(conn: sqlite3.Connection) -> None:
    df = pd.read_sql_query(
        "SELECT name, district, occupation, motive_score FROM suspects ORDER BY suspect_id",
        conn,
    )

    COLS = 5
    ROWS = 5  # 25 suspects total
    X_GAP = 2.2   # horizontal spacing
    Y_GAP = 4.2   # vertical spacing (row height)

    fig = go.Figure()

    # ── Police lineup backdrop ──────────────────────────────────────────────────
    # Background wall with height ruler lines
    wall_h = ROWS * Y_GAP + 1.0
    wall_w = COLS * X_GAP + 0.4
    fig.add_shape(type="rect", x0=-0.6, y0=-0.2, x1=wall_w, y1=wall_h,
                  fillcolor="#0a0f1e", line=dict(width=0), layer="below")

    # Height markers on the right wall (like a real lineup room)
    for tick_y in np.arange(0, wall_h, 0.5):
        fig.add_shape(type="line", x0=wall_w - 0.15, y0=tick_y,
                      x1=wall_w, y1=tick_y,
                      line=dict(color="#334155", width=1))
    for tick_y in np.arange(0, wall_h, 1.0):
        fig.add_annotation(x=wall_w + 0.05, y=tick_y, text=f"{tick_y:.0f}m",
                           showarrow=False, xanchor="left",
                           font=dict(color="#475569", size=7, family="Courier New"))

    # Spotlight circles per column (top of each column)
    for col in range(COLS):
        cx = col * X_GAP + 1.1
        for r in range(ROWS):
            cy_floor = r * Y_GAP
            # ground strip
            fig.add_shape(type="rect",
                          x0=col * X_GAP + 0.3, y0=cy_floor - 0.18,
                          x1=col * X_GAP + 1.9, y1=cy_floor,
                          fillcolor="#1e293b", line=dict(width=0), layer="below")

    # ── Draw each suspect as a stick figure ────────────────────────────────────
    for i, row in df.iterrows():
        col = i % COLS
        r   = i // COLS
        cx  = col * X_GAP + 1.1   # center x
        cy  = r   * Y_GAP          # floor y

        color = _DISTRICT_COLORS.get(row["district"], "#475569")
        score = row["motive_score"]
        # Shadow
        fig.add_shape(type="circle",
                      x0=cx - 0.45, y0=cy - 0.08,
                      x1=cx + 0.45, y1=cy + 0.04,
                      fillcolor="rgba(0,0,0,0.35)", line=dict(width=0), layer="above")
        # Legs
        fig.add_shape(type="line", x0=cx, y0=cy + 0.35,
                      x1=cx - 0.25, y1=cy,
                      line=dict(color=color, width=2.5), layer="above")
        fig.add_shape(type="line", x0=cx, y0=cy + 0.35,
                      x1=cx + 0.25, y1=cy,
                      line=dict(color=color, width=2.5), layer="above")
        # Body
        fig.add_shape(type="line", x0=cx, y0=cy + 0.35,
                      x1=cx, y1=cy + 1.15,
                      line=dict(color=color, width=3), layer="above")
        # Arms
        fig.add_shape(type="line", x0=cx - 0.35, y0=cy + 0.65,
                      x1=cx + 0.35, y1=cy + 0.65,
                      line=dict(color=color, width=2.5), layer="above")
        # Head
        fig.add_shape(type="circle",
                      x0=cx - 0.22, y0=cy + 1.15,
                      x1=cx + 0.22, y1=cy + 1.60,
                      fillcolor=color,
                      line=dict(color="white", width=1.5), layer="above")
        # Motive score badge (small dot on chest, brighter = higher score)
        badge_col = (
            "#ef4444" if score >= 8 else
            "#f59e0b" if score >= 5 else
            "#22c55e"
        )
        fig.add_shape(type="circle",
                      x0=cx - 0.10, y0=cy + 0.78,
                      x1=cx + 0.10, y1=cy + 0.98,
                      fillcolor=badge_col,
                      line=dict(color="white", width=1), layer="above")

        # Name above head — split first/last for readability
        parts = row["name"].split(" ", 1)
        label = parts[0] + "<br>" + parts[1] if len(parts) > 1 else row["name"]
        fig.add_annotation(
            x=cx, y=cy + 1.85,
            text=f"<b>{label}</b>",
            showarrow=False, xanchor="center",
            font=dict(color="white", size=8, family="Courier New"),
        )

        # Number card below feet
        fig.add_annotation(
            x=cx, y=cy - 0.32,
            text=f"#{i+1:02d}",
            showarrow=False, xanchor="center",
            font=dict(color="#475569", size=7, family="Courier New"),
        )

    # ── Title ───────────────────────────────────────────────────────────────────
    fig.add_annotation(
        x=wall_w / 2, y=wall_h + 0.35,
        text="🔦  POLICE LINE-UP  ·  ALL 25 SUSPECTS  ·  DO NOT SPEAK TO THE SUBJECTS",
        showarrow=False,
        font=dict(color="#93c5fd", size=11, family="Courier New"),
    )

    fig.update_layout(
        plot_bgcolor="#0a0f1e",
        paper_bgcolor="#0f172a",
        xaxis=dict(showgrid=False, showticklabels=False, range=[-0.7, wall_w + 0.5]),
        yaxis=dict(showgrid=False, showticklabels=False, range=[-0.7, wall_h + 0.7]),
        showlegend=False,
        height=640,
        margin=dict(l=0, r=30, t=10, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Legend
    legend_html = ' &nbsp; '.join(
        f'<span style="color:{c};">■</span> {d}'
        for d, c in _DISTRICT_COLORS.items()
    )
    st.markdown(
        f'<p style="font-size:11px; color:#64748b; font-family:Courier New;">'
        f'Figure color = district &nbsp;|&nbsp; {legend_html} &nbsp;|&nbsp; '
        f'Chest badge: <span style="color:#ef4444;">■</span> high motive &nbsp;'
        f'<span style="color:#f59e0b;">■</span> mid &nbsp;'
        f'<span style="color:#22c55e;">■</span> low</p>',
        unsafe_allow_html=True,
    )


def _viz_suspects_by_district(conn: sqlite3.Connection) -> None:
    """All 25 suspects: Docklands ones spotlit, the rest greyed out."""
    df = pd.read_sql_query(
        "SELECT name, district, occupation, motive_score FROM suspects ORDER BY suspect_id",
        conn,
    )
    face_b64 = _load_face_b64_list()
    use_faces = len(face_b64) >= 25
    docklands_color = _DISTRICT_COLORS["Docklands"]

    st.markdown(
        f'<div style="background:#060d1a; border:1px solid #1e293b; border-radius:8px;'
        f'padding:10px 16px 6px 16px; margin-bottom:10px;">'
        f'<span style="color:#93c5fd; font-family:Courier New; font-size:13px; letter-spacing:2px;">'
        f'🔍 WITNESS REPORT: PERPETRATOR LAST SEEN IN '
        f'<span style="color:{docklands_color};">DOCKLANDS</span>'
        f'</span></div>',
        unsafe_allow_html=True,
    )

    COLS = 5
    for row_start in range(0, 25, COLS):
        cols = st.columns(COLS)
        for col_idx, suspect_i in enumerate(range(row_start, min(row_start + COLS, 25))):
            suspect = df.iloc[suspect_i]
            is_docklands = suspect["district"] == "Docklands"
            score = int(suspect["motive_score"])
            badge_col = "#ef4444" if score >= 8 else "#f59e0b" if score >= 5 else "#22c55e"

            with cols[col_idx]:
                if use_faces:
                    img_b64 = face_b64[suspect_i] if suspect_i < len(face_b64) else ""
                    dim_style = "" if is_docklands else "filter:grayscale(90%) opacity(0.25);"
                    img_tag = (
                        f'<img src="data:image/jpeg;base64,{img_b64}"'
                        f' style="width:100%; border-radius:4px; display:block; {dim_style}" />'
                    )
                else:
                    img_tag = '<div style="height:80px; background:#1e293b; border-radius:4px;"></div>'

                if is_docklands:
                    border  = f"2px solid {docklands_color}"
                    pin     = f'<div style="font-size:9px; color:{docklands_color}; font-family:Courier New; margin-top:3px;">📍 DOCKLANDS</div>'
                    badge   = f'<div style="margin-top:3px;"><span style="background:{badge_col}; color:white; font-size:9px; border-radius:8px; padding:1px 6px; font-family:Courier New;">MOTIVE {score}/10</span></div>'
                    name_col = "white"
                    bg       = "#0a0f1e"
                else:
                    border   = "2px solid #1a2030"
                    pin      = ""
                    badge    = ""
                    name_col = "#2d3748"
                    bg       = "#060d1a"

                st.markdown(
                    f'<div style="background:{bg}; border:{border}; border-radius:8px;'
                    f'padding:5px; text-align:center; margin-bottom:4px;">'
                    f'{img_tag}'
                    f'<div style="font-family:Courier New; font-size:10px; color:{name_col};'
                    f'margin-top:4px; font-weight:bold; white-space:nowrap;'
                    f'overflow:hidden; text-overflow:ellipsis;">{suspect["name"]}</div>'
                    f'{pin}{badge}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    st.markdown(
        f'<p style="font-size:11px; color:#475569; font-family:Courier New; margin-top:6px;">'
        f'<span style="color:{docklands_color};">■</span> Docklands suspects (lit) &nbsp;·&nbsp;'
        f' greyed out = other districts &nbsp;·&nbsp;'
        f' your WHERE query returns only the 5 lit faces</p>',
        unsafe_allow_html=True,
    )


def _viz_motive_leaderboard(conn: sqlite3.Connection) -> None:
    """
    All 25 suspects as a face grid, ranked by motive score.
    Top 3 (ORDER BY result) get a gold crown + rank badge.
    The 2 remaining Docklands suspects get a red pin (overlap with Challenge 2).
    Everyone else is dimmed — making the convergence of district + motive visible.
    """
    df = pd.read_sql_query(
        "SELECT suspect_id, name, district, occupation, motive_score "
        "FROM suspects ORDER BY suspect_id",
        conn,
    )
    # Compute rank by motive score (1 = highest)
    df["rank"] = df["motive_score"].rank(method="first", ascending=False).astype(int)

    face_b64 = _load_face_b64_list()
    use_faces = len(face_b64) >= 25
    docklands_color = _DISTRICT_COLORS["Docklands"]
    gold = "#f59e0b"

    st.markdown(
        f'<div style="background:#060d1a; border:1px solid #1e293b; border-radius:8px;'
        f'padding:10px 16px 8px 16px; margin-bottom:10px;">'
        f'<span style="color:#93c5fd; font-family:Courier New; font-size:13px; letter-spacing:2px;">'
        f'🏆 TOP SUSPECTS BY MOTIVE SCORE — '
        f'<span style="color:{gold};">TOP 3 HIGHLIGHTED</span>'
        f'</span>'
        f'<div style="color:#475569; font-size:11px; font-family:Courier New; margin-top:4px;">'
        f'Notice: all 3 top-motive suspects are also from '
        f'<span style="color:{docklands_color};">Docklands</span> (Challenge 2 overlap — not a coincidence)'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    COLS = 5
    for row_start in range(0, 25, COLS):
        cols = st.columns(COLS)
        for col_idx, suspect_i in enumerate(range(row_start, min(row_start + COLS, 25))):
            suspect = df.iloc[suspect_i]
            rank       = int(suspect["rank"])
            score      = int(suspect["motive_score"])
            district   = suspect["district"]
            is_top3    = rank <= 3
            is_docklands_not_top3 = (district == "Docklands") and not is_top3

            with cols[col_idx]:
                if use_faces:
                    img_b64 = face_b64[suspect_i] if suspect_i < len(face_b64) else ""
                    if is_top3:
                        dim_style = ""
                    else:
                        dim_style = "filter:grayscale(90%) opacity(0.18);"
                    img_tag = (
                        f'<img src="data:image/jpeg;base64,{img_b64}"'
                        f' style="width:100%; border-radius:4px; display:block; {dim_style}" />'
                    )
                else:
                    img_tag = '<div style="height:80px; background:#1e293b; border-radius:4px;"></div>'

                if is_top3:
                    border   = f"2px solid {gold}"
                    bg       = "#1a1200"
                    name_col = "white"
                    crown    = f'<div style="font-size:11px; text-align:center; margin-bottom:2px;">👑 #{rank}</div>'
                    extra    = (
                        f'<div style="margin-top:3px;">'
                        f'<span style="background:{gold}; color:#0f172a; font-size:9px;'
                        f' border-radius:8px; padding:1px 6px; font-family:Courier New;">'
                        f'MOTIVE {score}/10</span></div>'
                        f'<div style="font-size:9px; color:{docklands_color};'
                        f' font-family:Courier New; margin-top:2px;">📍 DOCKLANDS</div>'
                    )
                elif is_docklands_not_top3:
                    border   = f"2px solid {docklands_color}"
                    bg       = "#0a0f1e"
                    name_col = "#94a3b8"
                    crown    = ""
                    extra    = (
                        f'<div style="font-size:9px; color:{docklands_color};'
                        f' font-family:Courier New; margin-top:3px;">📍 Docklands</div>'
                    )
                else:
                    border   = "2px solid #1a2030"
                    bg       = "#060d1a"
                    name_col = "#2d3748"
                    crown    = ""
                    extra    = ""

                st.markdown(
                    f'<div style="background:{bg}; border:{border}; border-radius:8px;'
                    f' padding:5px; text-align:center; margin-bottom:4px;">'
                    f'{crown}'
                    f'{img_tag}'
                    f'<div style="font-family:Courier New; font-size:10px; color:{name_col};'
                    f' margin-top:4px; font-weight:bold; white-space:nowrap;'
                    f' overflow:hidden; text-overflow:ellipsis;">{suspect["name"]}</div>'
                    f'{extra}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    st.markdown(
        f'<p style="font-size:11px; color:#475569; font-family:Courier New; margin-top:6px;">'
        f'<span style="color:{gold};">■</span> Top 3 by motive (your query result) &nbsp;·&nbsp;'
        f'<span style="color:{docklands_color};">■</span> Docklands (Challenge 2) — all 3 overlap &nbsp;·&nbsp;'
        f'greyed out = eliminated</p>',
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def _build_city_map_fig(crimes_tuple: tuple) -> go.Figure:
    """Build the Ravencroft city map figure. Cached — crime data never changes."""
    crimes = dict(crimes_tuple)
    max_c = max(crimes.values())

    # ── District layout on a 12 × 11 canvas ───────────────────────────────────
    # Each entry: (x0, y0, x1, y1, base_color)
    dists = [
        ("Northside",   2.1, 7.2, 11.8, 10.6, "#0d2545"),
        ("Old Quarter", 2.1, 3.7,  6.8,  7.2, "#2d1b00"),
        ("Docklands",   2.1, 0.2,  6.8,  3.7, "#0a200a"),
        ("Midtown",     6.8, 3.7, 11.8,  7.2, "#16163a"),
        ("Riverside",   6.8, 0.2, 11.8,  3.7, "#0a1e20"),
    ]

    fig = go.Figure()

    # ── Harbor / Water (left strip) ────────────────────────────────────────────
    fig.add_shape(type="rect", x0=-1.8, y0=-0.5, x1=2.2, y1=11.2,
                  fillcolor="#071628", opacity=1, line=dict(width=0), layer="below")
    # Animated-style wave lines
    for y_base in np.linspace(0.5, 10.5, 10):
        xs = np.linspace(-1.7, 2.1, 50)
        ys = y_base + 0.10 * np.sin(xs * 8 + y_base)
        fig.add_trace(go.Scatter(
            x=xs.tolist(), y=ys.tolist(), mode="lines",
            line=dict(color="#1e4d7a", width=0.8),
            hoverinfo="skip", showlegend=False,
        ))
    # Dock piers
    for yp, h in [(0.5, 0.55), (1.4, 0.45), (2.3, 0.55)]:
        fig.add_shape(type="rect", x0=0.1, y0=yp, x1=2.0, y1=yp + h,
                      fillcolor="#1a3020", line=dict(color="#374151", width=1), layer="above")
        fig.add_annotation(x=1.05, y=yp + h / 2, text="▬▬",
                           showarrow=False, font=dict(color="#475569", size=8))
    fig.add_annotation(x=0.2, y=5.5, text="H A R B O R",
                       textangle=-90, showarrow=False,
                       font=dict(color="#3b82f6", size=10, family="Courier New"))
    fig.add_annotation(x=0.2, y=5.5 - 1.8, text="⚓",
                       showarrow=False, font=dict(color="#3b82f6", size=14))

    # ── District fills ──────────────────────────────────────────────────────────
    for name, x0, y0, x1, y1, base_col in dists:
        n = crimes.get(name, 0)
        intensity = 0.4 + 0.6 * (n / max_c)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

        # Base fill (gets brighter with more crimes)
        fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                      fillcolor=base_col, opacity=intensity,
                      line=dict(color="#374151", width=2), layer="below")
        # Red heat overlay proportional to crimes
        heat = round(n / max_c * 0.35, 2)
        fig.add_shape(type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                      fillcolor=f"rgba(220,38,38,{heat})",
                      line=dict(width=0), layer="above")

        # ── Crime bar (filled/empty blocks) ─────────────────────────────────
        bar = "█" * n + "░" * (max_c - n)
        bar_color = ("#ef4444" if n >= 8 else "#f59e0b" if n >= 5 else "#22c55e")

        # District name
        fig.add_annotation(x=cx, y=cy + 0.55, text=f"<b>{name.upper()}</b>",
                           showarrow=False,
                           font=dict(color="white", size=11, family="Courier New"))
        # Crime count
        fig.add_annotation(x=cx, y=cy + 0.05,
                           text=f"<b>{n}</b> crimes",
                           showarrow=False,
                           font=dict(color=bar_color, size=15, family="Courier New"))
        # Bar
        fig.add_annotation(x=cx, y=cy - 0.45, text=bar,
                           showarrow=False,
                           font=dict(color=bar_color, size=8, family="Courier New"))

    # ── Streets ─────────────────────────────────────────────────────────────────
    # Crown Avenue (y=7.2)
    fig.add_shape(type="rect", x0=2.1, y0=7.05, x1=11.8, y1=7.35,
                  fillcolor="#78350f", opacity=0.9, line=dict(width=0), layer="above")
    fig.add_annotation(x=7, y=7.2, text="— CROWN AVE —",
                       showarrow=False, font=dict(color="#fbbf24", size=8, family="Courier New"))
    # Harbor Street (y=3.7)
    fig.add_shape(type="rect", x0=2.1, y0=3.55, x1=11.8, y1=3.85,
                  fillcolor="#78350f", opacity=0.9, line=dict(width=0), layer="above")
    fig.add_annotation(x=7, y=3.7, text="— HARBOR ST —",
                       showarrow=False, font=dict(color="#fbbf24", size=8, family="Courier New"))
    # Central Boulevard (x=6.8)
    fig.add_shape(type="rect", x0=6.65, y0=0.2, x1=6.95, y1=10.6,
                  fillcolor="#78350f", opacity=0.9, line=dict(width=0), layer="above")
    fig.add_annotation(x=6.8, y=5.5, text="CENTRAL BLVD",
                       textangle=-90, showarrow=False,
                       font=dict(color="#fbbf24", size=8, family="Courier New"))
    # Dock Road (x=2.1)
    fig.add_shape(type="rect", x0=1.95, y0=0.2, x1=2.25, y1=10.6,
                  fillcolor="#374151", opacity=0.8, line=dict(width=0), layer="above")

    # ── Northside landmarks ──────────────────────────────────────────────────────
    fig.add_shape(type="rect", x0=8.8, y0=8.1, x1=10.8, y1=9.9,
                  fillcolor="#14532d", opacity=0.65,
                  line=dict(color="#22c55e", width=1), layer="above")
    fig.add_annotation(x=9.8, y=9.0, text="🌳 PARK",
                       showarrow=False, font=dict(color="#86efac", size=9))
    # Police HQ
    fig.add_shape(type="rect", x0=3.0, y0=8.0, x1=5.0, y1=9.8,
                  fillcolor="#1e3a5f", opacity=0.8,
                  line=dict(color="#3b82f6", width=1), layer="above")
    fig.add_annotation(x=4.0, y=8.9, text="🏛️ HQ",
                       showarrow=False, font=dict(color="#93c5fd", size=9))

    # ── Riverside strip ──────────────────────────────────────────────────────────
    fig.add_shape(type="rect", x0=10.5, y0=0.2, x1=11.8, y1=3.7,
                  fillcolor="#071628", opacity=0.7, line=dict(width=0), layer="above")
    for y_base in np.linspace(0.5, 3.3, 5):
        xs = np.linspace(10.5, 11.8, 20)
        ys = y_base + 0.08 * np.sin(xs * 10)
        fig.add_trace(go.Scatter(
            x=xs.tolist(), y=ys.tolist(), mode="lines",
            line=dict(color="#1e4d7a", width=0.6),
            hoverinfo="skip", showlegend=False,
        ))
    fig.add_annotation(x=11.15, y=1.9, text="RIVER",
                       textangle=-90, showarrow=False,
                       font=dict(color="#3b82f6", size=9, family="Courier New"))

    # ── City title & compass ─────────────────────────────────────────────────────
    fig.add_annotation(x=7.0, y=11.25,
                       text="🏙️  C I T Y  O F  R A V E N C R O F T  ·  C R I M E  M A P  2 0 2 4",
                       showarrow=False,
                       font=dict(color="#93c5fd", size=12, family="Courier New"))
    fig.add_annotation(x=11.4, y=10.4, text="N\n▲",
                       showarrow=False, font=dict(color="#94a3b8", size=11))

    fig.update_layout(
        plot_bgcolor="#0a0f1e",
        paper_bgcolor="#0f172a",
        xaxis=dict(showgrid=False, showticklabels=False, range=[-1.8, 12.2]),
        yaxis=dict(showgrid=False, showticklabels=False, range=[-0.5, 11.5]),
        showlegend=False,
        height=480,
        margin=dict(l=0, r=0, t=10, b=0),
    )
    return fig


def _viz_crime_city_map(conn: sqlite3.Connection) -> None:
    df = pd.read_sql_query(
        "SELECT district, COUNT(*) AS crime_count FROM crimes GROUP BY district",
        conn,
    )
    crimes_tuple = tuple(sorted(zip(df["district"], df["crime_count"])))
    fig = _build_city_map_fig(crimes_tuple)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "🔴 District brightness = crime intensity. "
        "█ = crime, ░ = no crime. Docklands (10 crimes) glows the darkest red."
    )


def _viz_evidence_heatmap(conn: sqlite3.Connection) -> None:
    """
    All 25 suspects as a face grid.
    The 4 with Physical evidence are spotlit; Alex Crane gets a 🔪 overlay.
    Everyone else is dimmed.
    """
    df = pd.read_sql_query(
        "SELECT suspect_id, name, district, occupation, motive_score FROM suspects ORDER BY suspect_id",
        conn,
    )
    # Physical evidence suspect IDs (from db_setup seed: rows 1-4 → suspect_ids 1,2,3,11)
    physical_ids_df = pd.read_sql_query(
        "SELECT DISTINCT suspect_id FROM evidence WHERE evidence_type = 'Physical'", conn
    )
    physical_ids = set(physical_ids_df["suspect_id"].tolist())

    face_b64 = _load_face_b64_list()
    use_faces = len(face_b64) >= 25
    red = "#ef4444"

    st.markdown(
        f'<div style="background:#060d1a; border:1px solid #1e293b; border-radius:8px;'
        f'padding:10px 16px 8px 16px; margin-bottom:10px;">'
        f'<span style="color:#93c5fd; font-family:Courier New; font-size:13px; letter-spacing:2px;">'
        f'🔬 FORENSICS REPORT: SUSPECTS WITH '
        f'<span style="color:{red};">PHYSICAL EVIDENCE</span>'
        f'</span>'
        f'<div style="color:#475569; font-size:11px; font-family:Courier New; margin-top:4px;">'
        f'Your JOIN query reveals 4 suspects linked to physical evidence at crime scenes'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    COLS = 5
    for row_start in range(0, 25, COLS):
        cols = st.columns(COLS)
        for col_idx, suspect_i in enumerate(range(row_start, min(row_start + COLS, 25))):
            suspect = df.iloc[suspect_i]
            sid     = int(suspect["suspect_id"])
            is_physical = sid in physical_ids
            is_alex  = suspect["name"] == "Alex Crane"

            with cols[col_idx]:
                if use_faces:
                    img_b64 = face_b64[suspect_i] if suspect_i < len(face_b64) else ""
                    dim_style = "" if is_physical else "filter:grayscale(90%) opacity(0.18);"
                    img_tag = (
                        f'<img src="data:image/jpeg;base64,{img_b64}"'
                        f' style="width:100%; border-radius:4px; display:block; {dim_style}" />'
                    )
                else:
                    img_tag = '<div style="height:80px; background:#1e293b; border-radius:4px;"></div>'

                if is_physical:
                    border   = f"2px solid {red}"
                    bg       = "#1a0a0a"
                    name_col = "white"
                    knife    = '<div style="font-size:18px; text-align:center; margin-bottom:2px; line-height:1;">🔪</div>' if is_alex else '<div style="font-size:14px; text-align:center; margin-bottom:2px; line-height:1;">⚠️</div>'
                    badge    = (
                        f'<div style="margin-top:3px;">'
                        f'<span style="background:{red}; color:white; font-size:9px;'
                        f' border-radius:8px; padding:1px 6px; font-family:Courier New;">'
                        f'PHYSICAL EVIDENCE</span></div>'
                    )
                else:
                    border   = "2px solid #1a2030"
                    bg       = "#060d1a"
                    name_col = "#2d3748"
                    knife    = ""
                    badge    = ""

                st.markdown(
                    f'<div style="background:{bg}; border:{border}; border-radius:8px;'
                    f' padding:5px; text-align:center; margin-bottom:4px;">'
                    f'{knife}'
                    f'{img_tag}'
                    f'<div style="font-family:Courier New; font-size:10px; color:{name_col};'
                    f' margin-top:4px; font-weight:bold; white-space:nowrap;'
                    f' overflow:hidden; text-overflow:ellipsis;">{suspect["name"]}</div>'
                    f'{badge}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    st.markdown(
        f'<p style="font-size:11px; color:#475569; font-family:Courier New; margin-top:6px;">'
        f'<span style="color:{red};">■</span> Physical evidence found &nbsp;·&nbsp;'
        f'🔪 Alex Crane — primary suspect &nbsp;·&nbsp;'
        f'greyed out = no physical evidence</p>',
        unsafe_allow_html=True,
    )


def _viz_repeat_offenders(conn: sqlite3.Connection) -> None:
    df = pd.read_sql_query(
        """
        SELECT s.name, COUNT(*) AS evidence_count, s.district
        FROM evidence e
        JOIN suspects s ON e.suspect_id = s.suspect_id
        GROUP BY e.suspect_id
        ORDER BY evidence_count DESC
        """,
        conn,
    )
    df["color"] = df["evidence_count"].map(
        lambda c: "#ef4444" if c > 1 else "#475569"
    )
    fig = go.Figure(go.Bar(
        x=df["name"], y=df["evidence_count"],
        marker_color=df["color"],
        text=df["evidence_count"], textposition="outside",
        customdata=df[["district"]],
        hovertemplate="<b>%{x}</b><br>Evidence pieces: %{y}<br>District: %{customdata[0]}<extra></extra>",
    ))
    fig.add_hline(y=1.5, line_dash="dash", line_color="#f59e0b",
                  annotation_text="HAVING COUNT(*) > 1 threshold",
                  annotation_font_color="#f59e0b")
    _fig_layout(fig, "🚨 Repeat Offenders (red = appears in >1 evidence row)", height=380)
    fig.update_xaxes(gridcolor=_GRID, tickangle=-30)
    fig.update_yaxes(gridcolor=_GRID)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Red bars are the suspects your HAVING query should have found.")


# ── Hint panel ─────────────────────────────────────────────────────────────────

def render_hints(level_num: int, lvl: dict) -> None:
    hint_level = st.session_state.get(f"hint_level_{level_num}", 0)
    if hint_level >= 1:
        st.warning(f"💡 **Hint 1:** {lvl['hint1']}")
    if hint_level >= 2:
        st.info(f"💡 **Hint 2:** {lvl['hint2']}")


# ── Story update ───────────────────────────────────────────────────────────────

def render_story_update(level_num: int, completed_levels: set, all_done_text: str) -> None:
    if level_num not in completed_levels:
        return
    from levels import STORY_UPDATES, ALL_COMPLETE_TEXT
    if {1, 2, 3, 4, 5}.issubset(completed_levels) and level_num == max(completed_levels):
        text = ALL_COMPLETE_TEXT
    else:
        text = STORY_UPDATES.get(level_num, "")
    if text:
        st.markdown(
            f'<div class="story-update">📜 {text}</div>',
            unsafe_allow_html=True,
        )


# ── Lock panel ─────────────────────────────────────────────────────────────────

def render_lock_panel(level_num: int) -> None:
    prev = level_num - 1
    st.markdown(
        f'<div class="lock-panel">🔒 Complete Challenge {prev} to unlock this investigation.</div>',
        unsafe_allow_html=True,
    )


def render_avatar(message: str) -> None:
    """Render a fixed-position floating detective avatar with a speech bubble.

    Uses a zero-height components.html iframe whose script injects the avatar
    directly into window.parent.document.body — necessary because Streamlit's
    main container has overflow:auto which breaks position:fixed inside it.
    """
    import streamlit.components.v1 as components
    import html as _html

    safe_msg = _html.escape(message or "")

    components.html(
        f"""
        <script>
        (function() {{
            var msg = {repr(safe_msg)};
            var parentDoc = window.parent.document;

            // Remove any previous avatar
            var old = parentDoc.getElementById('sq-detective-avatar');
            if (old) old.remove();

            // No message — just clear and exit
            if (!msg) return;

            // Inject keyframe + avatar styles into parent <head> (once)
            if (!parentDoc.getElementById('sq-avatar-style')) {{
                var s = parentDoc.createElement('style');
                s.id = 'sq-avatar-style';
                s.textContent = `
                    #sq-detective-avatar {{
                        position: fixed;
                        bottom: 24px;
                        right: 24px;
                        z-index: 999999;
                        display: flex;
                        flex-direction: column;
                        align-items: flex-end;
                        gap: 4px;
                        max-width: 380px;
                        pointer-events: none;
                        font-family: sans-serif;
                    }}
                    #sq-detective-avatar .det-emoji {{
                        font-size: 80px;
                        line-height: 1;
                        filter: drop-shadow(0 2px 8px rgba(0,0,0,0.6));
                    }}
                    #sq-detective-avatar .det-bubble {{
                        background: #1e293b;
                        border: 2px solid #3b82f6;
                        border-radius: 18px 18px 2px 18px;
                        padding: 14px 18px;
                        color: #e2e8f0;
                        font-size: 15px;
                        line-height: 1.6;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
                        word-break: break-word;
                        max-width: 340px;
                        animation: sq-bubble-pop 0.35s cubic-bezier(0.175,0.885,0.32,1.275) both;
                    }}
                    @keyframes sq-bubble-pop {{
                        from {{ transform: scale(0.6) translateY(12px); opacity: 0; }}
                        to   {{ transform: scale(1)   translateY(0);    opacity: 1; }}
                    }}
                `;
                parentDoc.head.appendChild(s);
            }}

            // Build avatar element
            var wrap = parentDoc.createElement('div');
            wrap.id = 'sq-detective-avatar';
            wrap.innerHTML =
                '<div class="det-bubble">' + msg + '</div>' +
                '<div class="det-emoji">&#x1F575;&#xFE0F;</div>';
            parentDoc.body.appendChild(wrap);
        }})();
        </script>
        """,
        height=0,
    )
