# Big Data — SQL & Data Engineering Projects

Four interactive data applications built with Python, SQLite, and Streamlit, covering
data loading, ORM design, game development, and SQL education.

---

## Live Apps

| # | App | Link |
|---|---|---|
| 1 | Baby Names Explorer | [Open →](https://data-mining-in-large-databases-kuabme5kqccwyexedxh3mk.streamlit.app/) |
| 2 | Oscar Actor Explorer | [Open →](https://data-mining-in-large-databases-8wpo4fmnlfvbdukierwn7g.streamlit.app/) |
| 3 | Pokémon Battle Arena | [Open →](https://data-mining-in-large-databases-vaewz6c7ktlvxwhjdtezxz.streamlit.app/) |
| 4 | SQL Detective Agency | [Open →](https://data-mining-in-large-databases-3acrtu4hpzvegfbgfxpddg.streamlit.app/) |

---

## Table of Contents

- [Task 1 — Baby Names Explorer](#task-1--baby-names-explorer)
- [Task 2 — Oscar Actor Explorer](#task-2--oscar-actor-explorer)
- [Task 3 — Pokémon Battle Arena](#task-3--pokémon-battle-arena)
- [Task 4 — SQL Detective Agency](#task-4--sql-detective-agency)
- [Running Locally](#running-locally)
- [Repository Structure](#repository-structure)

---

## Task 1 — Baby Names Explorer

**[Live App](https://data-mining-in-large-databases-kuabme5kqccwyexedxh3mk.streamlit.app/)** · Dataset: US Social Security Administration baby names, 1880–2014 (~1.8 M rows) · Backend: SQLite via `sqlite3`

### What it does

A three-tab Streamlit web app for exploring 134 years of US baby-name data.

**Tab A — Name Popularity Over Time**
Enter one or more names (comma-separated) and see an interactive line chart across years.
Toggle between raw birth count and percentage of all births that year — the latter corrects
for US population growth and reveals genuine popularity shifts.

**Tab B — Custom SQL Query Panel**
A free-text SQL editor with five pre-built example queries:
- Top 10 names in 2010
- Gender-neutral names (balanced M & F usage)
- Names that disappeared after 1950
- Top name per decade (using `ROW_NUMBER() OVER PARTITION BY`)
- Name diversity per year

All queries are safety-checked (SELECT-only) before execution. Results are rendered as a
sortable table; if the result contains a numeric and a time/categorical column, an automatic
chart section appears with axis selectors and a Bar / Line toggle.

**Tab C — Name Insights**
- *Name Diversity Over Time* — unique names per year by gender, showing the dramatic rise
  in naming individuality since the 1960s.
- *Peak Decade Finder* — enter any name to see its decade-by-decade popularity breakdown.

### Schema & indexes

```sql
CREATE TABLE national_names (
    Id      INTEGER PRIMARY KEY,
    Name    TEXT    NOT NULL,
    Year    INTEGER NOT NULL,
    Gender  TEXT    NOT NULL,
    Count   INTEGER NOT NULL
);
-- Indexes: idx_nat_name (Name), idx_nat_year (Year), idx_nat_name_year (Name, Year)
```

The composite `(Name, Year)` index acts as a covering index for the relative-popularity
query, reducing it to a pure index seek. Benchmark in `task1_baby_names.ipynb` measures a
**50–80× speedup** vs full-table scan.

### Notable findings (Task 1.3)

| Finding | Key number |
|---|---|
| Linda's Baby-Boom spike — two 1930s films + a #1 Billboard hit + the post-war birth surge compounded into the largest single-year jump in 134 years | +47,072 births in 1947 |
| Ashley was male for 90 years before a 1982 soap opera triggered a near-complete gender flip | 1880–1950: male; 1980s: 352k female vs 5k male |
| Top-10 names went from 22% of all births (1880s) to 5% (2010s) — a 4× collapse in naming conformity | 22.4% → 5.1% over 130 years |

### Files

```
task1/
├── app.py                  # Streamlit app (Task 1.2)
├── task1_baby_names.ipynb  # Data loading, schema, index benchmarks (Task 1.1)
├── baby_names.db           # SQLite database (~395 MB)
└── docs/
    ├── readme_task1_1.md
    ├── readme_task1_2.md
    └── readme_task1_3.md
```

---

## Task 2 — Oscar Actor Explorer

**[Live App](https://data-mining-in-large-databases-8wpo4fmnlfvbdukierwn7g.streamlit.app/)** · Dataset: The Oscar Award, 11,110 nominations, 97 ceremonies, 1927–2024 · Backend: PonyORM (Python 3.11)

### What it does

Search any Academy Award nominee by name and see a rich profile card combining Oscar
database records with a live Wikipedia biography.

**Profile card sections:**
- Header with Wikipedia photo and a link to the biography page
- Five key metrics: Nominations, Wins, Win Rate, First Nominated, Last Nominated
- First-win callout (green / blue / orange banner based on career arc)
- Wikipedia biography extract
- Nominated categories list
- *vs. Category Average* table — how this person's nomination count compares to the mean across all nominees in each of their categories
- *Did You Know?* — a deterministically selected fun fact (nomination percentile, career span, win streak)
- Full nomination history table (film, year, category, win)

### ORM schema

Five normalised PonyORM entities:

| Entity | PK | Notes |
|---|---|---|
| `Ceremony` | `number` | 97 ceremonies |
| `Category` | auto | 118 raw names → 58 canonical |
| `Person` | auto | 6,893 distinct nominees |
| `Film` | auto | composite unique `(title, year)` |
| `Nomination` | auto | FK to all four above; `person` and `film` Optional |

All queries use PonyORM generator expressions — no raw SQL anywhere.

### Notable findings (Task 2.3)

| Finding | Detail |
|---|---|
| **Angela Lansbury** holds the record for longest gap between first nomination and first win: **69 years** (1945 nomination → 2014 Honorary Award) | Reveals how Honorary Awards are used to compensate for careers overlooked in competitive voting |
| **Titanic (1997)** is the only film ever nominated in **14 distinct canonical categories** | Nearest competitors all sit at 13 (*Forrest Gump*, *Gone with the Wind*, *Oppenheimer*, *La La Land*) |
| Only **four individuals** have competitive nominations in all three primary filmmaking roles (Acting, Directing, Writing) | Woody Allen, John Huston, Kenneth Branagh, John Cassavetes — out of ~6,893 total nominees |

### Files

```
task2/
├── app2.py                      # Streamlit actor profile app (Task 2.2)
├── task2_oscar.ipynb            # ORM schema + data loading (Task 2.1)
├── task2_oscar_findings.ipynb   # Reproducible findings (Task 2.3)
├── oscar.db                     # SQLite database
├── .venv311/                    # Python 3.11 venv (PonyORM + Streamlit)
└── readme_task2_*.md
```

---

## Task 3 — Pokémon Battle Arena

**[Live App](https://data-mining-in-large-databases-vaewz6c7ktlvxwhjdtezxz.streamlit.app/)** · Dataset: 800 Pokémon (Gen 1–6) + full 18×18 type-effectiveness matrix · Backend: PonyORM (Python 3.11)

### What it does

A fully playable turn-based Pokémon battle game where all stats and type matchups are
read from a database — no hardcoded values.

**Three phases:**

1. **Team Setup** — Searchable multiselect to pick 1–3 Pokémon from all 800 in the DB.
   A live preview shows HP, ATK, DEF, Speed, Total, and legendary flag. The AI drafts
   its team randomly from the remaining pool.

2. **Battle** — Side-by-side layout with HP progress bars. Clicking **Attack!** resolves
   one full round using the damage formula:
   ```
   damage = max(1, floor(attacker.attack / defender.defense × 40 × type_mult))
   ```
   Turn order is determined by Speed. Type multipliers are looked up from the
   `TypeEffectiveness` table (all 324 ordered pairs stored, dual-type chains both multipliers).

3. **Results** — Win/loss banner, full turn-by-turn log, and a battle history table
   (results are written back to the `BattleLog` table in the DB).

### Cheat Codes (Task 3.3)

Five real database write operations triggered by entering codes during battle:

| Code | DB Operation | Effect |
|---|---|---|
| `UPUPDOWNDOWN` | UPDATE — doubles HP for each player Pokémon | |
| `GODMODE` | UPDATE — sets active Pokémon's DEF and SP.DEF to 999 | |
| `STEAL` | INSERT — copies AI's strongest Pokémon to player's team | |
| `NERF` | UPDATE — halves all six stats for every AI Pokémon | |
| `LEGENDARY` | INSERT — adds custom "UltraMewtwo" (780 Total) to player's team | |

A **Cheat Audit** section on the results screen queries the DB for anomalous stat values
(DEF ≥ 999, HP > 255, names matching `"Stolen %"`, name = `"UltraMewtwo"`) to detect
which cheats were used across all past sessions.

### Analytical findings (Task 3.4)

- **Power creep is real:** non-legendary Pokémon average ~+7–10 Total per generation over Gen 1–6. A Gen 6 starter has roughly the same base Total as a Gen 1 mid-tier Pokémon with one evolution.
- **Dragon-types dominate by design:** Dragon's high average Total is explained by Game Freak deliberately placing pseudo-legendaries and box legendaries in the Dragon category — removing them brings Dragon's average close to Water and Psychic non-legendary averages.

### Files

```
task3/
├── app3.py                 # Battle game + cheat codes (Tasks 3.2 & 3.3)
├── task3_pokemon.ipynb     # Schema, data loading, analysis (Tasks 3.1 & 3.4)
├── pokemon.db              # SQLite database
└── readme_task3_*.md
```

---

## Task 4 — SQL Detective Agency

**[Live App](https://data-mining-in-large-databases-3acrtu4hpzvegfbgfxpddg.streamlit.app/)** · Purpose: teach SQL to beginners through a story-driven detective game · Backend: SQLite via `sqlite3`

### What it does

The learner plays a detective who solves cases by writing real SQL queries against a
crime database. Each of the five main cases (plus one unlockable bonus) teaches exactly one
SQL concept in pedagogical order:

| Case | Concept | Task |
|---|---|---|
| 1 — Open the Case Files | `SELECT *` | Retrieve all 25 suspects |
| 2 — Narrow the Suspects | `WHERE` | Filter to the Docklands district |
| 3 — Top Suspects | `ORDER BY / LIMIT` | Rank suspects by motive score |
| 4 — Crime by District | `GROUP BY / COUNT` | Count crimes per district |
| 5 — Connect the Evidence | `JOIN` | Link suspects to physical evidence |
| Bonus — The Mastermind | `HAVING` | Find suspects with multiple evidence records |

Levels unlock sequentially. Progress is persisted to the database (UUID session ID) so
refreshing the page restores completed levels, points, and badges.

**Answer checking:** the learner's query is executed against the real DB and the resulting
DataFrame is compared by row count, column set, and key cell values — never by string matching.
Every level has a `diagnose_fn` that returns a specific message explaining *what* is wrong
(not just "incorrect").

### Engagement features (Task 4.2)

**Detective Rank System** — points awarded per solve (15 / 10 / 5 depending on attempts)
unlock five ranks from *Rookie Constable* to *Master Detective*. Rank-ups fire `st.balloons()`.

**Badge System** — six badges earned for specific achievements (first case closed, no hints used, first-try solve, persistence after using both hints, all five cases, bonus level).

**Hot Streak Tracker** — consecutive first-try no-hint solves increment a streak counter.
At 3+ consecutive, an amber "🔥 You're on fire!" banner appears in the sidebar.

**Visual SQL Teaching Aids:**
- Level 3 shows a before/after sort comparison (unsorted vs `ORDER BY motive_score DESC`)
- Level 5 shows a side-by-side `suspects ↔ evidence` JOIN diagram with the join key annotated
- Level 2 highlights matching WHERE rows yellow using `pandas Styler`

**Floating Detective Avatar** — a fixed-position detective emoji with a speech bubble
reacts to game events: welcomes the player by name, congratulates level completions,
announces badge unlocks, explains SQL errors and wrong answers in character voice.
Implemented via `streamlit.components.v1.html` (parent-document injection) to achieve
true viewport-fixed positioning.

**Story Narrative** — a story update box appears after each solve, advancing a crime
narrative that gives the learner a concrete reason to understand the next SQL concept.

### Files

```
task4/
├── app4.py          # Main Streamlit app
├── db_setup.py      # Schema creation, seeding, safe_execute
├── levels.py        # Level definitions (story, task, hints, check_fn, diagnose_fn)
├── progress.py      # detective_log DB read/write, badge logic
├── ui_components.py # Reusable widgets + floating avatar
├── styles.py        # CSS theme string
├── agency.db        # SQLite database (created at runtime)
└── readme_task4_*.md
```

---

## Running Locally

All four apps require Python 3.11 (PonyORM is incompatible with Python 3.14).
A shared virtual environment is used across Tasks 2–4.

```bash
# Clone the repository
git clone <repo-url>
cd "Big Data scraping"

# Create the Python 3.11 venv (once)
python3.11 -m venv task2/.venv311
task2/.venv311/Scripts/pip install streamlit pandas plotly ponyorm requests

# Task 1
streamlit run task1/app.py

# Task 2 (generate oscar.db first by running task2/task2_oscar.ipynb)
task2/.venv311/Scripts/streamlit run task2/app2.py

# Task 3 (generate pokemon.db first by running task3/task3_pokemon.ipynb)
task2/.venv311/Scripts/streamlit run task3/app3.py

# Task 4
task2/.venv311/Scripts/streamlit run task4/app4.py
```

---

## Repository Structure

```
.
├── requirements.txt          # Streamlit Cloud deployment dependencies
├── task1/                    # Baby Names Explorer
│   ├── app.py
│   ├── task1_baby_names.ipynb
│   ├── baby_names.db
│   └── docs/
├── task2/                    # Oscar Actor Explorer
│   ├── app2.py
│   ├── task2_oscar.ipynb
│   ├── task2_oscar_findings.ipynb
│   ├── oscar.db
│   └── .venv311/             # Shared Python 3.11 venv
├── task3/                    # Pokémon Battle Arena
│   ├── app3.py
│   ├── task3_pokemon.ipynb
│   └── pokemon.db
└── task4/                    # SQL Detective Agency
    ├── app4.py
    ├── db_setup.py
    ├── levels.py
    ├── progress.py
    ├── ui_components.py
    └── styles.py
```

Each task folder contains per-subtask `readme_task<X>_<Y>.md` files with full implementation
details, technology choices, challenges encountered, and interesting findings.
