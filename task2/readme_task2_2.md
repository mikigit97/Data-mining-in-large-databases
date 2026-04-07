# Task 2.2 – Actor Profile App

## What I Built and How It Works

`app2.py` is a Streamlit app that lets a user search for any Academy Award nominee by
name and instantly see a rich profile card. The app pulls from two sources: the
`oscar.db` SQLite database (via PonyORM, same schema built in Task 2.1) and the
Wikipedia REST API.

**Search flow:**
1. User types a partial or full name in the sidebar text box.
2. A PonyORM generator expression performs a case-insensitive substring search across
   all 6,893 `Person` records: `select(p.name for p in Person if q in p.name.lower())`.
3. If multiple matches are found, a radio list lets the user pick one.
4. The profile and Wikipedia data are loaded (and cached) for the selected person.

**Profile card sections:**
- **Header** — Wikipedia thumbnail photo (if available) and the person's name with a
  link to their Wikipedia page.
- **Key metrics** — five `st.metric` tiles: Nominations, Wins, Win Rate, First Nominated,
  Last Nominated.
- **First-win callout** — a coloured banner (green / blue / orange) depending on whether
  they won at their very first ceremony, had to wait, or have never won.
- **Biography** — the Wikipedia extract fetched from the REST summary endpoint.
- **Categories** — the canonical Oscar categories the person was nominated in.
- **vs. Category Average** — a table showing, for each category, how this person's
  nomination count compares to the average across all nominees in that same category.
- **Did You Know?** — a deterministically chosen fun fact generated from the data
  (nomination percentile, win streak, career span, etc.).
- **Nomination History** — a full sortable table of every nomination with film, year,
  category, and win indicator.

**How to run:**
```
task2/.venv311/Scripts/streamlit run task2/app2.py
```
Requires `streamlit` and `requests` installed in the `.venv311` Python 3.11 environment
(`pip install streamlit requests`). PonyORM and pandas are already present.

---

## Technologies & Libraries

| Technology | Why chosen |
|---|---|
| **PonyORM 0.7.19** | Same ORM used in Task 2.1. All DB queries use generator expressions (`select(n for n in Nomination if n.person == person)`) with no raw SQL. `@db_session` and `with db_session:` manage connection lifetime. |
| **Streamlit** | Turns a plain Python script into an interactive web app with zero HTML/JS. `st.metric`, `st.dataframe`, `st.columns`, and `@st.cache_data` / `@st.cache_resource` provide the UI and caching layer with minimal code. |
| **Wikipedia REST API** (`/api/rest_v1/page/summary/`) | Returns a clean JSON object with `extract` (plain-text bio), `thumbnail.source` (profile photo URL), and `content_urls.desktop.page` (link). Simpler and more reliable than the `wikipedia` Python package for obtaining thumbnails. No authentication required. |
| **requests** | Standard HTTP client for the Wikipedia API call with a timeout and a descriptive `User-Agent` header. |
| **pandas** | Used only for constructing `pd.DataFrame` objects fed to `st.dataframe`. |

**Why no raw SQL:** PonyORM's generator syntax is expressive enough to cover all required
queries — filtering, grouping with `count()`, joining across relations — without falling
back to `db.execute()`.

---

## Challenges & Solutions

**1. `@st.cache_data` + `@db_session` decorator stacking**
Applying both decorators directly to one function caused PonyORM to receive cache-hit
calls without an active session, then attempt to lazy-load entity attributes and raise
`DatabaseSessionIsOver`.
Fix: split into a public `get_profile()` function decorated with `@st.cache_data` and a
private `_load_profile()` decorated with `@db_session`. On first call, `_load_profile`
runs inside a session and returns a plain Python dict; on subsequent calls, `get_profile`
returns the cached dict without touching the DB.

**2. `Database.bind()` called more than once on Streamlit reruns**
Streamlit re-executes the entire script on every interaction. Calling `db.bind()` a second
time raises `TypeError: The database object was already bound to...`.
Fix: wrapped `db.bind()` and `db.generate_mapping()` in a `@st.cache_resource` function
(`_init_db`). Streamlit calls it only once for the lifetime of the server process.

**3. Wikipedia disambiguation pages returned as valid results**
Some names (e.g. "Peter Jackson") resolve to a disambiguation page. The REST API returns
`{"type": "disambiguation"}` rather than an error status.
Fix: inspect `d.get("type")` in `_try()` and return `None` for disambiguation or
`no-extract` responses. A fallback loop then retries with common suffixes:
`(actor)`, `(actress)`, `(film director)`, `(composer)`.

**4. Deterministic "Did You Know?" across reruns**
The fact is chosen from a list using `random.choice`, but Streamlit reruns the script on
every widget interaction, causing the displayed fact to change every time.
Fix: seed the random generator with the person's name before selecting
(`random.seed(name)`), then immediately reset the seed so other parts of the app are
not affected. The same person always shows the same fact.

**5. `readonly=True` invalid kwarg crashes on startup**
PonyORM's SQLite provider passes extra `db.bind()` kwargs directly to `sqlite3.connect()`,
which does not accept a `readonly` parameter. This raised
`TypeError: 'readonly' is an invalid keyword argument for Connection()` before any page
rendered.
Fix: replaced `readonly=True` with `create_db=False`, which is PonyORM's own supported
argument to prevent creating a new DB file if the path doesn't exist.

**6. `ERDiagramError: Mapping is not generated for entity 'Person'` on first search**
Streamlit re-executes the entire script module on every user interaction. With entity
classes defined at module level, each rerun created a new `Database()` instance with
freshly-defined entity classes. `@st.cache_resource` correctly skipped re-running
`db.bind()` — but it called `bind()` on the *old* Database object, not the new one
created in the latest rerun. Queries against the new unbound entities then failed.
Fix: moved `Database()`, all entity class definitions, `db.bind()`, and
`db.generate_mapping()` inside the `@st.cache_resource` function and returned the
entity classes as a tuple. Module-level names are re-assigned from the cached tuple on
every rerun, ensuring all query functions always reference the one bound Database and its
mapped entity classes.

**7. Wikipedia REST API does not return birth date**
The `/api/rest_v1/page/summary/` endpoint used for biography and photo does not include
structured birth date data. Parsing it from the `extract` text with regex is unreliable
(date formats vary and many extracts omit the date entirely).
Fix: two-step Wikidata lookup. First, the Wikipedia Action API
(`?action=query&prop=pageprops&ppprop=wikibase_item`) returns the Wikidata entity ID (QID)
for the page. Second, the Wikidata Action API (`?action=wbgetentities&props=claims`)
returns all structured claims; property P569 (date of birth) gives an ISO timestamp
(`+1949-06-22T00:00:00Z`) that is parsed and formatted to `June 22, 1949`.

**8. Two simultaneous input widgets created conflicting state**
The sidebar originally showed both a dropdown (10 notable nominees) and a free-text search
box at the same time. A user could select "Katharine Hepburn" from the dropdown while
"Meryl Streep" remained typed in the search box, making it unclear which name the app
would use. The dropdown was given priority in code, but this was invisible to the user.
Fix: replaced both widgets with a `st.radio` mode toggle ("Pick from list" / "Search by
name"). Selecting a mode renders only its corresponding input widget — the other is never
shown. This eliminates the ambiguity entirely: only one input exists at any given time.

**9. Per-category comparison query is slow for nominees in many categories**
The category comparison runs one `select(...count...)` query per canonical category.
A person nominated in 10 categories triggers 10 round-trips.
Fix: acceptable for a homework app (each query is fast on a 11,110-row SQLite DB) and
the result is cached by `@st.cache_data`, so the cost is paid only on the first lookup.

---

## Interesting Findings

**Meryl Streep is definitively the most-nominated actor in Academy history (21 nominations, 3 wins).**
The category comparison table shows she was nominated in Best Actress (Leading Role) 17
times — a ratio of 3.5× the category average of ~4.8 nominations per nominee. Her win rate
of 14% is below her category's overall win rate, illustrating how dominant presence in the
nomination stage does not linearly translate to wins.

**Peter O'Toole received 8 nominations and 0 wins — the most nominations of any actor with
no win.**
The "Did You Know?" card surfaces this as a notable zero-win streak fact. His
never-winning record earned him an Honorary Award in 2003, which appears separately in the
dataset under the `HONORARY AWARD` canonical category.

**The "vs. Category Average" table reveals how concentrated Oscar nominations are.**
In categories like Best Original Score (Music), the average nominee has ~1.2 nominations.
John Williams (47 nominations) has a ratio of ~39×, showing he occupies a structural
position in that category unlike any other composer.
