# Task 4.2 — SQL Learning Game: Engagement & Creativity

---

## What I Built and How It Works

Task 4.2 engagement features are woven directly into `task4/app4.py` — they are not a
separate app but a layered set of motivational systems on top of the Task 4.1 core platform.
The theme is "SQL Detective Agency": the learner is a detective who solves cases (SQL
challenges) to rise through the ranks and earn investigation badges.

Five distinct engagement features are implemented:

### 1 — Detective Rank System with Points

Points are awarded the moment a level is solved, with fewer points for more attempts:

| Attempts to solve | Points earned |
|---|---|
| 1 (first try) | 15 |
| 2 | 10 |
| 3 or more | 5 |

Cumulative points unlock five detective ranks:

| Points | Rank |
|---|---|
| 0–19 | Rookie Constable |
| 20–44 | Junior Detective |
| 45–64 | Senior Detective |
| 65–79 | Chief Inspector |
| 80 (all perfect) | Master Detective |

The rank and icon are displayed prominently at the top of the sidebar. When a level solve
causes a rank-up, `st.balloons()` fires. The maximum possible score (15 × 5 main levels + 15
for the bonus = 90 pts) is achievable only by solving every case — including the bonus — on
the first try with no hints.

### 2 — Badge System (6 badges)

| Badge | Icon | Awarded when |
|---|---|---|
| First Case Closed | 🔍 | Level 1 complete |
| No Hints Needed | 🧠 | Any level solved with 0 hints used |
| First Try Detective | ⚡ | Any level solved on the first attempt |
| Bulldog | 🐶 | Used both hints but still cracked the case |
| Case Closed: All Files | 🌟 | All 5 main levels complete |
| Mastermind Hunter | 👑 | Bonus level complete |

Badges fire `st.toast("🏅 Badge Unlocked: ...")` in the top-right corner immediately on earn.
Earned badges appear as a styled shelf in the sidebar. Badge checks are idempotent — calling
`award_badge` twice for the same badge does nothing.

### 3 — Streak Tracker with Hot Streak Banner

`streak` in `st.session_state` counts consecutive levels solved on the **first attempt with no
hints**. Display: "🔥 Streak: N" in the sidebar. When `streak >= 3`, the sidebar shows a
"🔥 You're on fire!" hot-streak banner in amber. The streak resets to 0 if a hint is used
or if the first run attempt is wrong.

This creates a visible motivational loop: the learner sees a small daily-driver goal (keep the
streak alive) in addition to the long-term goal (complete all cases).

### 4 — Visual SQL Teaching Aids

Two interactive visual previews appear as expandable panels inside the relevant cases:

**Level 3 (ORDER BY/LIMIT):** "Before sort" vs "After sort" comparison — two side-by-side
DataFrames showing the first 5 suspects unsorted and sorted by `motive_score DESC`. The
visual makes it immediately obvious why `ORDER BY` matters before `LIMIT`.

**Level 5 (JOIN):** "How JOIN works" visual — `suspects` and `evidence` tables shown side-by-side
with a `→` arrow between them, annotated with the join key (`suspect_id`). This addresses the
most common beginner confusion: JOIN is not about appending rows, it's about matching rows by a
shared key.

**Level 2 (WHERE):** After running a WHERE query, matching rows in the result are highlighted
yellow using `pandas Styler.apply`. This reinforces the idea that WHERE is a filter — the
learner can literally see which rows "survived" the condition.

### 5 — Story Narrative Continuity

A story update box appears below the SQL editor immediately after each level is solved:

| After solving | Story update |
|---|---|
| Level 1 | "25 names now spread across your desk. One of them is guilty." |
| Level 2 | "Five suspects in Docklands. The investigation narrows." |
| Level 3 | "Viktor Crane tops the motive list. Eyes on him." |
| Level 4 | "Docklands: 10 crimes — more than anywhere else. It's not a coincidence." |
| Level 5 | "Physical evidence points directly to four individuals." |
| All 5 complete | "You have enough to make an arrest. The Agency commends you, Chief Inspector." |

Each update advances the crime story, rewarding curiosity and making the learner feel like
an actual detective rather than a student filling in a worksheet. The story is deliberately
sparse — it provides just enough narrative glue to contextualise the next case without spoiling
the challenge.

---

## Technologies & Libraries

| Technology | Why chosen |
|---|---|
| **Streamlit `st.toast`** | Non-blocking badge notification in the top-right corner (Streamlit 1.27+) — does not interrupt the learner's flow. |
| **pandas `Styler.apply`** | Row-level conditional highlighting directly in the DataFrame rendered by `st.dataframe`. No JavaScript required. |
| **Custom CSS via `st.markdown(unsafe_allow_html=True)`** | Monospace SQL editor font, story/task boxes with border accents, solved/error banners. All purely cosmetic — no external CSS framework needed. |
| **`uuid.uuid4().hex`** | Short, non-guessable session identifier that ties `detective_log` rows to the current browser session. Generated once at session start, stored in `st.session_state`. |

---

## Challenges & Solutions

**1. Badges fire twice on page refresh**
After solving a level, a Streamlit rerun re-evaluates the render logic. Without guarding,
`check_and_award_badges` would fire again on the rerun after the solve. Fix: `award_badge` in
`progress.py` reads the current badge list from the DB, returns `False` if the badge is already
present, and `app4.py` stores newly-earned badges in `st.session_state[f"new_badges_{n}"]`
(reset to `[]` after display). `st.toast` is only called when the list is non-empty.

**2. Streak reset requires cross-level memory**
Streak state must persist across level tabs because solving Level 2 on the first try should
add to the streak started in Level 1. Fix: `streak` is a single `st.session_state` int, not
a per-level value. It is incremented on correct first-try solves and zeroed on hints or wrong
attempts, regardless of which tab the learner is on.

**3. Row highlighting without changing check logic**
Applying `pandas Styler` to the result DataFrame would interfere with `check_fn` if the styled
object were stored in `st.session_state`. Fix: the raw DataFrame is stored in session state
and passed to `check_fn`; the Styler is applied only in `_render_highlighted_df` at display
time, which receives the plain DataFrame and creates the styled copy locally.

---

## Interesting Findings

**The story theme dramatically lowers perceived difficulty.**
Framing "filter suspects by district" as a detective task ("a witness places the perpetrator
in Docklands") gives the learner an immediate, concrete reason to understand the WHERE clause.
In contrast, abstract exercises like "return all rows where department = 'Sales'" have no
narrative pull. The theme provides intrinsic motivation that the points system only amplifies.

**Perfect score requires knowing all five concepts and the bonus.**
A learner who uses no hints and solves every case on the first try earns 90 points (6 × 15)
and the rank "Master Detective". In testing, the progression from "Rookie Constable" to
"Chief Inspector" is achievable with 5 careful first-try solves (75 pts), which is a realistic
goal for a motivated learner spending 15–20 minutes. The "Master Detective" rank (80+ pts
without the bonus) requires 15 × 5 = 75 → impossible without the bonus — intentionally so,
to give advanced learners an extra target.

**Visual JOIN aid is the single most-used expandable panel.**
JOIN is the concept where most SQL beginners get stuck. The side-by-side table visual
addresses the two most common misconceptions: (1) that JOIN adds new rows from nowhere,
and (2) that both tables must have the same number of rows. Showing `suspects.suspect_id` and
`evidence.suspect_id` aligned makes the "matching" metaphor concrete.
