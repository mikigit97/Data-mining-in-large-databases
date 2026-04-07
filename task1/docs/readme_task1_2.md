# Task 1.2 – Interactive Name Explorer App

## What I Built and How It Works

I built a multi-tab interactive web application (`app.py`) using **Streamlit** that lets users
explore the US Baby Names dataset (1880–2014, ~1.8 M records) stored in the SQLite database
created in Task 1.1. The app is organized into three tabs:

### Tab A — Name Popularity Over Time
The user types one or more names (comma-separated) into a text box. The app queries
`national_names` for each name, groups by `Year` and `Gender`, and renders an interactive
Plotly line chart. A radio toggle switches between two display modes:
- **Raw count** — the absolute number of babies given that name each year.
- **% of births that year** — divides each name's count by the total births that year
  (computed via a pre-aggregated `GROUP BY Year` query), yielding relative popularity.
  This corrects for US population growth and makes cross-era comparisons fair.

### Tab B — Custom SQL Query Panel
A free-text SQL editor backed by five pre-built example queries loadable from a dropdown:
1. *Top 10 names in 2010*
2. *Gender-neutral names (balanced M & F)*
3. *Names that disappeared after 1950*
4. *Top name per decade*
5. *Name diversity per year*

On execution the app checks that the statement starts with `SELECT` before passing it to
SQLite; any other keyword triggers a friendly error message. Results are shown as a
`st.dataframe` table. If the result contains at least one numeric and one categorical column,
an automatic chart section appears with axis selectors and a Bar / Line toggle.

### Tab C — Name Insights (Additional Visualisation)
Two side-by-side panels:
- **Name Diversity Over Time** — a line chart of unique names registered per year, split by
  gender. Results are cached with `@st.cache_data` so the heavy aggregation only runs once.
- **Peak Decade Finder** — the user enters any name; the app groups total births into decades
  and shows a metric card ("Mary peaked in the 1910s — 3.7 M births") plus a colour-coded
  bar chart of all decades.

---

## Technologies & Libraries

| Technology | Why chosen |
|---|---|
| **Streamlit** | Fastest path from a Python script to a shareable web app; no HTML/CSS/JS needed. Natively supports text inputs, radio buttons, dropdowns, and tabs — all the interactive elements required by the task. |
| **Plotly Express** | Produces interactive, zoomable, hoverable charts with a single function call. Compared to Matplotlib, it requires no manual axis labelling and renders beautifully inside Streamlit via `st.plotly_chart`. |
| **pandas** | `pd.read_sql` cleanly bridges SQLite query results and Plotly/Streamlit data frames. Used for all data retrieval and for the merge that computes relative popularity. |
| **sqlite3** | Required by the assignment. The connection is created once with `@st.cache_resource` so it persists across Streamlit reruns without re-opening the file each interaction. |
| **Playwright MCP** (`@playwright/mcp`) | Browser automation MCP server that gives Claude live tools to navigate, click, fill inputs, and take full-page screenshots of the running Streamlit app. Used during development to visually verify UI rendering and catch layout bugs that are invisible from code alone. Configured globally in `~/.claude.json` and runs via `npx @playwright/mcp@latest`. |

Streamlit Cloud was chosen as the deployment target (preferred by the assignment) because it
reads `requirements.txt` directly from the repository and serves the app with one click.

---

## Challenges & Solutions

**1. Streamlit reruns the entire script on every widget interaction**
Every time the user types a character, Streamlit re-executes `app.py` from top to bottom.
Without caching, the expensive `COUNT(DISTINCT Name) GROUP BY Year` diversity query (scanning
7.5 M rows) would fire on every keystroke.
Solution: `@st.cache_resource` on the connection function and `@st.cache_data` on the
diversity query, so those results are computed once and reused for the session lifetime.

**2. Relative popularity requires a second query and a join**
The "% of births" mode needs the total births per year as a denominator — a value not present
in the per-name result set.
Solution: Run a separate aggregation (`SELECT Year, SUM(Count) AS Total FROM national_names
GROUP BY Year`) and merge it with the name DataFrame on `Year` using `df.merge(totals,
on="Year")`. Because the totals are small (135 rows) the merge is instantaneous.

**3. Auto-chart logic must handle varied query shapes**
The SQL panel receives arbitrary user queries, so the result schema is unknown in advance.
The chart section needs to decide on its own which column is the X-axis and which is the
Y-axis.
Solution: Classify columns as numeric (`select_dtypes("number")`) vs categorical (everything
else). If `Year` is present it becomes the default X-axis; otherwise the first categorical
column is used. Users can then override with dropdown selectors.

**4. SQL injection / accidental data modification**
A free-text SQL box could accept `DROP TABLE` or `DELETE FROM`.
Solution: Extract the first whitespace-delimited token of the query, uppercase it, and
compare to `"SELECT"`. Any other token causes Streamlit to display an error and skip
execution entirely.

**5. Bug discovered at runtime — SQL safety check bypassed by leading comments**
After running the app, a static code review revealed that the original safety check
(`cleaned.split()[0].upper()`) could be tricked by a query prefixed with a `--` comment
line (e.g. `-- SELECT\nDROP TABLE names`). The first token would be `--`, not `SELECT`,
causing the check to incorrectly block the query — but more importantly, rearranging the
comment order could bypass the intent entirely.
Fix: replaced the single-token check with a loop that skips all leading `--` comment
lines before extracting the first real keyword.

**8. Example query "Top name per decade" returned only decade 1880**
`ORDER BY Decade ASC, Total DESC LIMIT 20` simply returns the 20 most popular names
within the first (1880) decade rather than one winner per decade.
Fix: rewrote the query using `ROW_NUMBER() OVER (PARTITION BY decade ORDER BY SUM(Count) DESC)`
in a subquery, then filtered to `rn = 1`. Result: exactly one row per decade (14 rows, 1880–2010).

**7. Chart axis logic redesigned — arbitrary axis selection produced meaningless combinations**
Free axis selectors (X, Y, Color all user-chosen) allowed nonsensical charts such as
`x=Name, y=Year` or `color=Year` (135 distinct values → unreadable legend).
Fix: chart logic now enforces fixed roles. *Bar chart* — X-axis is user-selectable (any
column including Year/Decade); Y-axis is fixed to the count/measure column; Color is
always Gender (if present in the result), never anything else. *Line chart* — only
offered when a Year column is present; X is fixed to Year; Y is fixed to the measure
column; color encodes Name, or Name (M) / Name (F) if Gender is also in the result.
This eliminates all meaningless combinations while still supporting the full set of
meaningful layouts.

**6. Bug discovered at runtime — inner join silently drops rows in relative popularity mode**
The original `df.merge(totals, on="Year")` used pandas' default inner join. If any year
present in the name query result was absent from the totals table (edge case with sparse
data), those rows would be silently dropped, producing an incomplete chart.
Fix: changed to `how="left"` to preserve all name rows, and added `.replace(0, 1)` on the
`Total` column to guard against division-by-zero for any year with no recorded births.

---

## Interesting Findings

**Relative vs raw popularity tells very different stories.**
In raw-count mode, names like "Emma" appear to be surging to all-time highs in the 2000s.
Switching to "% of births" reveals they are still far below their 1880–1920 peaks — the
apparent surge is mostly explained by US population growth. The toggle makes this immediately
visible and teaches an important lesson about normalising time-series data.

**The gender-neutral query surface names that most people would not expect.**
Running the pre-built gender-neutral query (names with > 5 000 recorded births for both M and
F) returns names like *Casey*, *Riley*, *Jessie*, and *Marion*. What is striking is the
temporal pattern: many of these names started overwhelmingly male, crossed over to female use
in the mid-20th century, and then faded for males almost entirely — a pattern clearly visible
in Tab A.

**Name diversity has grown dramatically since the 1960s.**
The diversity chart in Tab C shows that the number of unique female names roughly tripled
between 1960 and 2010, while male name diversity grew more modestly. This reflects the broader
cultural shift toward individualism and away from naming children after saints or relatives —
a trend quantifiable here for the first time in the raw SSA data.
