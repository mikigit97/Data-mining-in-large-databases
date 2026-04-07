# HW1 — The Art of Analyzing Big Data: Task Reference

**Course:** The Art of Analyzing Big Data — Dr. Michael Fire

---

## General Guidelines

.
- **Every task requires a written report (1–2 pages)** covering:
  1. What you built and how it works
  2. Technologies/libraries chosen and why
  3. Challenges encountered and how you solved them
  4. Interesting findings
- **Submission format (pick one per task, deployed preferred):**
  - Deployed web app (Streamlit Cloud / HuggingFace / GitHub Pages / Colab)
  - Jupyter/Colab notebook with interactive widgets
  - Screen recording (3–5 min, narrated) on YouTube or Google Drive
  - GitHub repo with README + screenshots

---

## Task 1: Baby Names Explorer (25pt) ✅

**Dataset:** US Baby Names — `NationalNames.csv` (required), `StateNames.csv` (optional)
**Backend:** SQLite via `sqlite3` Python package

### Task 1.1 — Data Loading & Schema Design (5pt) ✅
- Load CSV into SQLite with columns: `Id, Name, Year, Gender, Count` (+ `State` if using state data)
- Create **at least 2 indexes**; justify each in a markdown cell (which queries they speed up and why)

### Task 1.2 — Interactive Name Explorer App (15pt) ✅
Must include **all** of:

**A. Name Popularity Over Time**
- Text input: one or more comma-separated names → line chart of popularity across years
- Toggle: raw count vs. percentage of all births that year (relative popularity)

**B. Custom SQL Query Panel**
- Free-text box to type and run any SELECT query
- Results shown as table; if result has a numeric + time/categorical column → offer bar or line chart
- At least **3 pre-built example queries** in a dropdown (e.g. "Top 10 names in 2010", "Gender-neutral names", "Names that disappeared after 1950")
- Safety: only allow SELECT; friendly error for any non-SELECT

**C. One Additional Visualization (your choice)**
Options (or invent your own):
- Animated bar chart race of top names per decade
- Gender-neutral name finder
- "Your name's peak decade" feature
- Name diversity over time (unique names per year)

### Task 1.3 — Pattern Discovery (10pt) ⏳
Find and report **3 interesting patterns** in the data. For each pattern:
1. State the finding clearly
2. Show the query or visualization that reveals it
3. Write a one-paragraph interpretation (what might explain this pattern?)

**Examples of valid patterns:**
- Cultural shifts in naming trends
- Name popularity spikes after celebrity events
- Gender crossover names (name starts as male, shifts to female or vice versa)
- Increasing name diversity over time
- Regional differences (if using state data)

---

## Task 2: Oscar Actor Explorer (25pt)

**Dataset:** The Oscar Award dataset
**Backend:** ORM — PonyORM, SQLAlchemy, or Peewee (your choice). **No raw SQL allowed.**

### Task 2.1 — Data Modeling with ORM (5pt)
- Load dataset into SQLite via chosen ORM
- Define entity/model classes with proper types, relationships, constraints
- Markdown cell: explain schema design and why you chose this ORM over others

### Task 2.2 — Actor Profile App (10pt)
User enters actor/director name → rich profile card combining:

**From dataset:**
- Number of nominations and wins
- Categories nominated in
- Years active at the Oscars
- List of nominated and winning films

**From Wikipedia (live via Wikipedia API or `wikipedia` Python package):**
- Short biography summary
- Birth date and photo (if available)

**Computed insights:**
- Win rate (wins / nominations)
- Comparison to average nominee in their category
- Years between first nomination and first win (if applicable)

Handle edge cases: actor not found, ambiguous Wikipedia matches, actors with no wins.

**Bonus (5pt):** "Did You Know?" feature — auto-generates a fun fact when user looks up any actor (e.g., "Meryl Streep has more nominations than 85% of all Oscar-nominated actors").

### Task 2.3 — Interesting Finds (10pt)
Find and report **3 interesting discoveries** using the app and/or ORM queries.
For each: state the finding, show how you found it, explain why it's interesting.

**Examples:**
- Actors with the most nominations but zero wins
- Longest gap between first nomination and first win
- Directors also nominated as actors (or vice versa)
- Categories with the most unique winners (hardest to predict)
- Actors/films with nominations across the most different categories

---

## Task 3: Pokémon Battle Arena (25pt)

**Dataset:** Pokémon Dataset (comprehensive stats)
**Backend:** SQLite via `sqlite3` or any ORM. **All stats must be read from the database — no hardcoded values.**

### Task 3.1 — Data Loading & Schema (5pt)
- Load into SQLite: `Name, Type1, Type2, HP, Attack, Defense, Sp.Atk, Sp.Def, Speed, Generation, Legendary`
- May add extra tables (e.g. type-effectiveness table, battle history log)
- Markdown cell: explain schema choices

### Task 3.2 — Battle Game (10pt)
Playable Pokémon-style battle (text-based, widget, or full app) with:
- **Team selection:** each player picks 1–3 Pokémon from database
- **Battle mechanics from data:** damage, turn order, effectiveness calculated from DB columns (Speed → turn order, Attack vs. Defense → damage); document your formula
- **Type advantage:** simplified type-effectiveness system (e.g. Fire > Grass > Water > Fire) stored in a DB table
- **Battle log:** display each turn (who attacked, damage dealt, super-effective or not)
- **Win condition:** game ends when all Pokémon on one side faint (HP ≤ 0)

Player vs. Player or Player vs. AI (AI can use random moves).

### Task 3.3 — Cheat Codes (5pt)
Implement at least **3 cheats** that execute **real SQL/ORM write operations** (INSERT/UPDATE/DELETE):
- `UPUPDOWNDOWN` — doubles your Pokémon's HP (UPDATE)
- `GODMODE` — sets your Defense and Sp.Def to 999 (UPDATE)
- `STEAL` — copies opponent's strongest Pokémon to your team (INSERT)
- `LEGENDARY` — inserts a custom overpowered Pokémon (INSERT)
- `NERF` — reduces all opponent stats by 50% (UPDATE)

After game ends: demonstrate a **"cheat audit" query** that detects which cheats were used (e.g. Pokémon with stats exceeding the dataset's natural maximum).

### Task 3.4 — Pokémon Analysis (5pt)
Write SQL/ORM queries to find and report **2 interesting insights**, e.g.:
- Which type combination is most overpowered on average?
- Is there statistical evidence of power creep across generations?
- What is the optimal 3-Pokémon team based purely on stats?
- Which Legendary Pokémon is statistically the weakest?

---

## Task 4: SQL Learning Game (25pt + bonus)

**Goal:** Build an interactive game/platform that teaches SQL to beginners (target: someone who has never written SQL).
**Best/most creative solution earns bonus points on final grade.**

### Task 4.1 — Core Platform (15pt)
Must include:
- A real SQLite database with at least one preloaded dataset for learners to query
- Interactive SQL input where the learner writes and executes real queries
- **At least 5 progressive challenges/levels** teaching SQL in order:
  - Level 1: `SELECT *`
  - Level 2: `WHERE`
  - Level 3: `ORDER BY` / `LIMIT`
  - Level 4: `GROUP BY` / aggregations
  - Level 5: `JOIN`
- **Feedback system:** check if learner's query returns the correct result; if wrong, provide a helpful hint explaining what went wrong (not just "incorrect")
- **Progress tracking:** learner sees which levels they completed

### Task 4.2 — Engagement & Creativity (10pt)
Make it genuinely fun. Ideas:
- Story-driven (detective solving crimes via queries, wizard casting SQL spells, space explorer querying star charts)
- Gamification (points, streaks, leaderboard, timed challenges, achievements, badges)
- Visual (show tables visually, animate JOIN/GROUP BY, highlight rows a WHERE selects)
- Adaptive difficulty (offer simpler sub-challenges if learner struggles)
- Multiplayer/competitive (two players race to solve challenges)
- AI-powered hints (LLM API generates personalized hints from learner's incorrect query)

**Submission for Task 4:**
- Short demo video (2–3 min)
- README explaining design choices and SQL concepts the platform teaches

---

## Status Tracker

| Task | Points | Status | Files |
|---|---|---|---|
| 1.1 Data Loading & Schema | 5pt | ✅ Done | `task1_baby_names.ipynb`, `readme_task1.md` |
| 1.2 Interactive Name Explorer | 15pt | ✅ Done | `app.py`, `readme_task1_2.md` |
| 1.3 Pattern Discovery | 10pt | ⏳ Pending | — |
| 2.1 ORM Data Modeling | 5pt | ⏳ Pending | — |
| 2.2 Actor Profile App | 10pt | ⏳ Pending | — |
| 2.3 Interesting Finds | 10pt | ⏳ Pending | — |
| 3.1 Pokémon Schema | 5pt | ⏳ Pending | — |
| 3.2 Battle Game | 10pt | ⏳ Pending | — |
| 3.3 Cheat Codes | 5pt | ⏳ Pending | — |
| 3.4 Pokémon Analysis | 5pt | ⏳ Pending | — |
| 4.1 Core Platform | 15pt | ⏳ Pending | — |
| 4.2 Engagement & Creativity | 10pt | ⏳ Pending | — |
| 2.2 Bonus (Did You Know?) | 5pt | ⏳ Pending | — |
