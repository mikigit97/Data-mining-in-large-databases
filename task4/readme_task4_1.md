# Task 4.1 — SQL Learning Game: Core Platform

---

## What I Built and How It Works

`task4/app4.py` is a Streamlit app that teaches SQL to beginners through the "SQL Detective
Agency" — a story-driven game where the learner plays a detective querying a crime database
to solve cases. Each of the five main cases (plus one unlockable bonus) teaches exactly one
SQL concept in pedagogical order.

**App structure:**

The app is split across five modules:
- `db_setup.py` — SQLite schema creation, data seeding, `safe_execute` query runner
- `levels.py` — Level definitions (story, task, hints, `check_fn`, `diagnose_fn` per level)
- `progress.py` — DB read/write for `detective_log` (progress persistence across refreshes)
- `ui_components.py` — Reusable Streamlit widgets (sidebar, hint panel, visual aids)
- `styles.py` — CSS injected via `st.markdown` (monospace editor, story boxes, banners)

**How to run:**
```
task2/.venv311/Scripts/streamlit run task4/app4.py
```

---

## Database (`agency.db`)

Four SQLite tables created at runtime by `db_setup.py`:

| Table | Rows | Purpose |
|---|---|---|
| `suspects` | 25 | Core dataset for Levels 1–3 |
| `crimes` | 28 | Crime reports for Level 4 (GROUP BY) |
| `evidence` | 30 | Links suspects to crimes for Level 5 (JOIN) |
| `detective_log` | 1 per (session, level) | Progress persistence + badge storage |

The data is seeded deliberately:
- **5 suspects** in `district = 'Docklands'` → Level 2 answer is 5 rows
- **Top-3 motive_scores** are `[9, 9, 8]` in that order → Level 3 answer is deterministic
- **10 crimes** in Docklands → Level 4 top row is always `('Docklands', 10)`
- **4 evidence rows** with `evidence_type = 'Physical'` → Level 5 answer is 4 rows

---

## Five Levels (+ Bonus)

| Case | SQL Concept | Task | Answer check |
|---|---|---|---|
| 1 — Open the Case Files | `SELECT *` | Get all columns from `suspects` | 25 rows, 7 expected columns |
| 2 — Narrow the Suspects | `WHERE` | Filter to `district = 'Docklands'` | 5 rows, all district=='Docklands' |
| 3 — Top Suspects | `ORDER BY` / `LIMIT` | Sort by `motive_score DESC LIMIT 3` | 3 rows, scores `[9,9,8]` in order |
| 4 — Crime by District | `GROUP BY` / `COUNT` | Count crimes per district, name col `crime_count` | 5 rows, first row Docklands/10 |
| 5 — Connect the Evidence | `JOIN` | JOIN suspects+evidence on `suspect_id`, filter `Physical` | 4 rows, cols `{name,district,evidence_type}` |
| Bonus — The Mastermind | `HAVING` | suspects with >1 evidence row | len≥2, all counts≥2 |

Levels unlock sequentially — Level 2 is locked until Level 1 is solved, etc. The Bonus
level unlocks only after all 5 main cases are complete.

**Answer checking strategy:** the learner's query is executed against the real DB via
`pd.read_sql_query`, and the resulting DataFrame is compared by shape + column names +
key cell values — never by SQL string matching. This means `SELECT name, age, ... FROM suspects`
and `SELECT * FROM suspects` both pass Level 1 as long as all 25 rows and 7 columns are present.

**Feedback system:** each level has a `diagnose_fn(df, query)` that returns a specific
message — e.g. "25 rows returned — you need a WHERE clause" or "3 rows but wrong order
— did you sort DESC?". The feedback explains *what* went wrong, not just "incorrect".

---

## Technologies & Libraries

| Technology | Why chosen |
|---|---|
| **SQLite via `sqlite3`** | Learners write raw SQL against a real database — using PonyORM or SQLAlchemy would abstract away the SQL the learner should be writing. `pd.read_sql_query` converts results to DataFrames automatically. |
| **Streamlit** | Reuses the same venv as Tasks 2–3. `@st.cache_resource` keeps a single DB connection for the app lifetime. `st.tabs` provides natural per-level navigation without page reloads. |
| **pandas** | `pd.read_sql_query` runs queries and returns DataFrames. `df.style.apply` provides row-level highlighting for visual feedback. |
| **Python 3.11 (`.venv311`)** | Same venv as Tasks 2–3; all required packages already installed. |

---

## Challenges & Solutions

**1. Progress survives browser refresh**
`st.session_state` alone resets on refresh, which would wipe level completion. Fix: progress
is persisted to a `detective_log` SQLite table using a UUID `session_id` (generated once and
stored in `st.session_state`). On every page load, the app reads the DB to restore completed
levels, points, and badges before rendering.

**2. SQL can be written many equivalent ways**
Checking `SELECT * FROM suspects` vs `SELECT suspect_id, name, age, ... FROM suspects` by
string comparison would be brittle. Fix: execute the query, then compare the resulting
DataFrame by row count and column set (order-insensitive). Level 3 additionally checks
the ordered values of `motive_score` because sort order matters there.

**3. SQL safety in an educational context**
The learner writes arbitrary SQL, so a `DROP TABLE suspects` would destroy the game data.
Fix: `safe_execute` checks that the query starts with `SELECT` and scans for a forbidden-token
regex (`drop|delete|insert|update|alter|create|...`). SQLite errors (malformed queries, wrong
table names) are caught and surfaced as readable messages.

**4. `st.tabs` cannot be disabled**
Streamlit provides no API to grey out individual tabs. Rendering just a lock message inside
a locked tab (instead of the editor) achieves the same gating effect without hacks.

**5. `mark_complete` must be idempotent**
If the learner refreshes after solving a level, the page reruns and could re-award points.
Fix: `mark_complete` reads the `completed` flag from the DB before writing, and the caller
guards on `if level_num not in st.session_state.completed_levels`.

---

## Interesting Findings

**Sequential unlocking reinforces pedagogy.**
Locking higher levels until prerequisite levels are solved prevents learners from skipping
to JOIN before understanding WHERE, which mirrors how SQL is actually taught in courses.
The story narrative provides an in-world reason for the progression ("we need more leads
before we can cross-reference evidence") rather than presenting it as an arbitrary gate.

**Deterministic seeding is critical for answer checking.**
Levels 3 and 4 require specific ordering in the result. This forced careful seeding design —
the Docklands crime count (10) is exactly double the next highest (5 each for Northside and
Old Quarter), making the ORDER BY answer unambiguous. The motive scores of 9/9/8 were also
chosen to include a tie at rank 1, verifying that the learner's ORDER BY handles ties correctly.
