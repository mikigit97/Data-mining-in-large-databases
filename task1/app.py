import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

_HERE = Path(__file__).parent
_DB_PATH = _HERE / "baby_names.db"
_CSV_PATH = _HERE / "us baby names" / "NationalNames.csv"


def _bootstrap_db(conn: sqlite3.Connection) -> None:
    """Create schema and load NationalNames.csv. Called only when DB is missing."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS national_names (
            Id      INTEGER PRIMARY KEY,
            Name    TEXT    NOT NULL,
            Year    INTEGER NOT NULL,
            Gender  TEXT    NOT NULL,
            Count   INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS state_names (
            Id      INTEGER PRIMARY KEY,
            Name    TEXT    NOT NULL,
            Year    INTEGER NOT NULL,
            Gender  TEXT    NOT NULL,
            State   TEXT    NOT NULL,
            Count   INTEGER NOT NULL
        );
        PRAGMA synchronous = OFF;
        PRAGMA journal_mode = MEMORY;
    """)
    if _CSV_PATH.exists():
        for chunk in pd.read_csv(str(_CSV_PATH), chunksize=50_000):
            chunk.to_sql("national_names", conn, if_exists="append", index=False)
    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_nat_name      ON national_names(Name);
        CREATE INDEX IF NOT EXISTS idx_nat_year      ON national_names(Year);
        CREATE INDEX IF NOT EXISTS idx_nat_name_year ON national_names(Name, Year);
        PRAGMA synchronous = FULL;
        PRAGMA journal_mode = DELETE;
    """)
    conn.commit()


# ── Connection (cached so it's reused across reruns) ────────────────────────
@st.cache_resource
def get_conn():
    needs_seed = not _DB_PATH.exists()
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    if needs_seed:
        with st.spinner("Building database from CSV — first launch only, ~30 seconds…"):
            _bootstrap_db(conn)
    return conn

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="US Baby Names Explorer",
    page_icon="👶",
    layout="wide",
)
st.title("👶 US Baby Names Explorer")
st.caption("US Social Security Administration data · 1880–2014 · ~1.8 M records")

con = get_conn()

tab1, tab2, tab3 = st.tabs(["📈 Name Popularity", "🔍 SQL Query Panel", "💡 Name Insights"])


# ════════════════════════════════════════════════════════════════════════════
# TAB A — Name Popularity Over Time
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Name Popularity Over Time")

    col_input, col_gender, col_mode = st.columns([3, 1, 1])
    with col_input:
        names_raw = st.text_input(
            "Name(s) — comma-separated",
            value="Emma, Olivia, Liam",
            placeholder="e.g. Emma, Liam, Mary",
        )
    with col_gender:
        gender_filter = st.radio(
            "Gender",
            ["Both", "Female only", "Male only"],
            help="Filter the chart to show only the selected gender(s).",
        )
    with col_mode:
        mode = st.radio(
            "Display mode",
            ["Raw count", "% of births that year"],
            help="'% of births' shows relative popularity, correcting for population growth.",
        )

    names = [n.strip().title() for n in names_raw.split(",") if n.strip()]

    if not names:
        st.info("Enter at least one name above.")
    else:
        # Build gender clause
        if gender_filter == "Female only":
            gender_clause = "AND Gender = 'F'"
        elif gender_filter == "Male only":
            gender_clause = "AND Gender = 'M'"
        else:
            gender_clause = ""

        placeholders = ",".join("?" * len(names))
        df = pd.read_sql(
            f"SELECT Year, Name, Gender, SUM(Count) AS Count "
            f"FROM national_names WHERE Name IN ({placeholders}) {gender_clause} "
            f"GROUP BY Year, Name, Gender ORDER BY Year",
            con,
            params=names,
        )

        if df.empty:
            st.warning(f"No records found for: {', '.join(names)}. Check spelling?")
        else:
            if mode == "% of births that year":
                totals = pd.read_sql(
                    "SELECT Year, SUM(Count) AS Total FROM national_names GROUP BY Year",
                    con,
                )
                df = df.merge(totals, on="Year", how="left")
                df["Count"] = (df["Count"] / df["Total"].replace(0, 1) * 100).round(4)
                y_label = "% of all births"
            else:
                y_label = "Count"

            df["Label"] = df["Name"] + " (" + df["Gender"] + ")"
            fig = px.line(
                df, x="Year", y="Count", color="Label",
                labels={"Count": y_label, "Label": "Name (Gender)"},
                title=f"Popularity of: {', '.join(names)}",
                markers=False,
            )
            fig.update_layout(hovermode="x unified", legend_title="Name (Gender)")
            st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB B — Custom SQL Query Panel
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Custom SQL Query Panel")
    st.markdown(
        "Run any **SELECT** query against the database. "
        "Tables available: `national_names`, `state_names`."
    )

    EXAMPLES = {
        "Top 10 names in 2010": (
            "SELECT Name, SUM(Count) AS Total\n"
            "FROM national_names\n"
            "WHERE Year = 2010\n"
            "GROUP BY Name\n"
            "ORDER BY Total DESC\n"
            "LIMIT 10"
        ),
        "Gender-neutral names (balanced M & F, all time)": (
            "SELECT Name,\n"
            "  SUM(CASE WHEN Gender='M' THEN Count ELSE 0 END) AS Male,\n"
            "  SUM(CASE WHEN Gender='F' THEN Count ELSE 0 END) AS Female\n"
            "FROM national_names\n"
            "GROUP BY Name\n"
            "HAVING Male > 5000 AND Female > 5000\n"
            "ORDER BY ABS(Male - Female) ASC\n"
            "LIMIT 20"
        ),
        "Names that disappeared after 1950": (
            "SELECT DISTINCT Name\n"
            "FROM national_names\n"
            "WHERE Year <= 1950\n"
            "  AND Name NOT IN (\n"
            "    SELECT DISTINCT Name FROM national_names WHERE Year > 1950\n"
            "  )\n"
            "ORDER BY Name\n"
            "LIMIT 30"
        ),
        "Top name per decade (all time)": (
            "SELECT Decade, Name, Total\n"
            "FROM (\n"
            "  SELECT (Year/10)*10 AS Decade, Name, SUM(Count) AS Total,\n"
            "         ROW_NUMBER() OVER (\n"
            "           PARTITION BY (Year/10)*10\n"
            "           ORDER BY SUM(Count) DESC\n"
            "         ) AS rn\n"
            "  FROM national_names\n"
            "  GROUP BY (Year/10)*10, Name\n"
            ")\n"
            "WHERE rn = 1\n"
            "ORDER BY Decade"
        ),
        "Name diversity per year (unique names)": (
            "SELECT Year, COUNT(DISTINCT Name) AS UniqueNames\n"
            "FROM national_names\n"
            "GROUP BY Year\n"
            "ORDER BY Year"
        ),
    }

    selected_example = st.selectbox(
        "Load an example query:",
        ["-- choose --"] + list(EXAMPLES.keys()),
    )

    default_sql = (
        EXAMPLES[selected_example]
        if selected_example != "-- choose --"
        else "SELECT * FROM national_names LIMIT 10"
    )

    sql = st.text_area("SQL Query", value=default_sql, height=160)
    run_btn = st.button("▶ Run Query", type="primary")

    # Run query and persist result in session state so view-switching doesn't clear it
    if run_btn:
        cleaned = sql.strip()
        first_word = ""
        for line in cleaned.splitlines():
            line = line.strip()
            if line and not line.startswith("--"):
                first_word = line.split()[0].upper()
                break
        if first_word != "SELECT":
            st.error(
                "Only **SELECT** statements are allowed. "
                "Queries that modify data (INSERT, UPDATE, DELETE, DROP, etc.) are blocked for safety."
            )
            st.session_state.pop("query_result", None)
        else:
            try:
                st.session_state["query_result"] = pd.read_sql(cleaned, con)
            except Exception as e:
                st.error(f"Query error: {e}")
                st.session_state.pop("query_result", None)

    # Render results if available (persists across reruns caused by view-switch)
    if "query_result" in st.session_state:
        result_df = st.session_state["query_result"]
        st.success(f"{len(result_df):,} row(s) returned.")

        cols = result_df.columns.tolist()
        all_num_cols = result_df.select_dtypes("number").columns.tolist()
        id_like = {c for c in all_num_cols if c.lower() == "id" or c.lower().endswith("_id")}
        num_cols = [c for c in all_num_cols if c not in id_like]

        has_year   = "Year"   in cols
        has_name   = "Name"   in cols
        has_gender = "Gender" in cols

        # Y-axis: the count/measure column — skip time-dimension columns (Year, Decade)
        _time_dims = {"year", "decade"}
        y_col = next((c for c in num_cols if c.lower() not in _time_dims), num_cols[0] if num_cols else None)

        # Bar: needs a numeric Y and at least one other column for X
        bar_x_options = [c for c in cols if c != y_col] if y_col else []
        can_bar  = bool(y_col and bar_x_options and len(result_df) > 1)
        # Line: needs Year column AND a separate numeric column for Y
        can_line = bool(has_year and y_col and y_col.lower() not in _time_dims and len(result_df) > 1)

        view_options = ["Table"]
        if can_bar:
            view_options.append("Bar chart")
        if can_line:
            view_options.append("Line chart")
        view = st.radio("View", view_options, horizontal=True, key="view_mode")

        if view == "Table":
            st.dataframe(result_df, use_container_width=True)

        elif view == "Bar chart":
            # X-axis: user picks any column except the Y measure
            default_x = "Name" if "Name" in bar_x_options else bar_x_options[0]
            x_col = st.selectbox("X-axis", bar_x_options,
                                 index=bar_x_options.index(default_x), key="x_axis")

            bar_df = result_df.copy()
            # Cast time-dimension X to string → categorical axis (every tick shown)
            if x_col.lower() in _time_dims:
                bar_df[x_col] = bar_df[x_col].astype(str)

            _time_col_in_result = next(
                (c for c in bar_df.columns if c.lower() in _time_dims and c != x_col), None
            )

            if x_col == "Name" and _time_col_in_result:
                # X=Name with a time column present: one bar per (Name, Decade) pair,
                # grouped side-by-side so each decade is visually separate
                bar_df[_time_col_in_result] = bar_df[_time_col_in_result].astype(str)
                color_col = _time_col_in_result
                bar_text = None
                barmode = "group"
            elif x_col.lower() in _time_dims:
                # X=Decade/Year: single bar per time point, color by Name so bars
                # belonging to the same name share the same color
                bar_df[x_col] = bar_df[x_col].astype(str)
                color_col = "Name" if has_name else ("Gender" if has_gender else None)
                bar_text = "Name" if has_name else None
                barmode = "relative"
            else:
                color_col = "Gender" if (has_gender and x_col != "Gender") else None
                bar_text = None
                barmode = "relative"

            fig = px.bar(bar_df, x=x_col, y=y_col, color=color_col,
                         text=bar_text, barmode=barmode, labels={y_col: y_col})
            if bar_text:
                fig.update_traces(textposition="outside", cliponaxis=False)
            # Force every x value to appear as a tick (Plotly auto-skips by default)
            x_vals = list(dict.fromkeys(bar_df[x_col].tolist()))  # unique, order-preserved
            fig.update_xaxes(
                tickmode="array", tickvals=x_vals, ticktext=x_vals,
                 tickfont=dict(size=11),
            )
            st.plotly_chart(fig, use_container_width=True)

        elif view == "Line chart":
            # X = Year (fixed), Y = measure (fixed)
            # One line per Name; split by Gender if Gender column present
            plot_df = result_df.copy()
            if has_name and has_gender:
                plot_df["_label"] = plot_df["Name"] + " (" + plot_df["Gender"] + ")"
                color_col  = "_label"
                color_label = "Name (Gender)"
            elif has_name:
                color_col  = "Name"
                color_label = "Name"
            else:
                color_col  = None
                color_label = None
            fig = px.line(
                plot_df, x="Year", y=y_col, color=color_col,
                labels={y_col: y_col, "_label": color_label} if color_label else {y_col: y_col},
                markers=False,
            )
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB C — Name Insights  (additional visualisation)
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Name Insights")

    col_left, col_right = st.columns(2)

    # ── C1: Name Diversity Over Time ────────────────────────────────────────
    with col_left:
        st.markdown("#### 🌈 Name Diversity Over Time")
        st.markdown(
            "How many **unique names** were registered each year? "
            "Rising diversity reflects cultural pluralism and immigration."
        )

        @st.cache_data
        def load_diversity():
            return pd.read_sql(
                "SELECT Year, Gender, COUNT(DISTINCT Name) AS UniqueNames "
                "FROM national_names GROUP BY Year, Gender ORDER BY Year",
                get_conn(),
            )

        div_df = load_diversity()
        fig_div = px.line(
            div_df, x="Year", y="UniqueNames", color="Gender",
            title="Unique Baby Names per Year",
            color_discrete_map={"F": "hotpink", "M": "steelblue"},
            labels={"UniqueNames": "Unique names"},
        )
        fig_div.update_layout(hovermode="x unified")
        st.plotly_chart(fig_div, use_container_width=True)

    # ── C2: Peak Decade Finder ───────────────────────────────────────────────
    with col_right:
        st.markdown("#### 🏆 Peak Decade Finder")
        st.markdown("Which decade was a name most popular? Enter any name to find out.")

        peak_name = st.text_input("Name", value="Mary", key="peak_input")

        if peak_name.strip():
            canonical = peak_name.strip().title()
            peak_df = pd.read_sql(
                "SELECT (Year/10)*10 AS Decade, SUM(Count) AS Total "
                "FROM national_names WHERE Name = ? "
                "GROUP BY Decade ORDER BY Decade",
                con,
                params=[canonical],
            )

            if peak_df.empty:
                st.warning(f"No data found for **{canonical}**. Check spelling?")
            else:
                best = peak_df.loc[peak_df["Total"].idxmax()]
                st.metric(
                    label=f"Peak decade for '{canonical}'",
                    value=f"{int(best['Decade'])}s",
                    delta=f"{int(best['Total']):,} total births that decade",
                )
                fig_peak = px.bar(
                    peak_df, x="Decade", y="Total",
                    title=f"'{canonical}' — births by decade",
                    color="Total",
                    color_continuous_scale="Blues",
                    labels={"Total": "Total births"},
                )
                fig_peak.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig_peak, use_container_width=True)
