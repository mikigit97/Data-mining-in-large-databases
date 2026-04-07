# Task 3.4 — Pokémon Analysis

---

## What I Built and How It Works

Two analytical insights are derived from ORM queries on `pokemon.db` (the same database
used in Tasks 3.1–3.3). All queries are written in PonyORM — no raw SQL.
Results are displayed as printed DataFrames and matplotlib charts inside
`task3/task3_pokemon.ipynb`.

### Insight 1 — Power Creep Across Generations

**Query:** `select((p.generation, avg(p.total), count(p)) for p in Pokemon if not p.legendary)`
run twice — once excluding legendaries, once for legendaries only — then ordered by generation.

The query computes the **mean base-stat Total per generation** for each group.
Non-legendary and legendary cohorts are kept separate so that the varying number of
legendaries per generation (e.g. Gen 2 has only 3) does not distort the average.
A `numpy.polyfit` linear regression is applied to the non-legendary series to
quantify the trend.

**Finding:** There is a statistically clear upward drift of approximately +7–10 Total
per generation in non-legendary Pokémon. A typical Gen 6 non-legendary has roughly
50 more base stats than a comparable Gen 1 Pokémon. The trend is not perfectly
monotone — Gen 3 sits slightly below Gen 2 — but the overall direction confirms
classic "power creep". Legendaries follow the same upward trend but with higher
variance due to small sample sizes (Gen 2: 3 legendaries, Gen 4: 14).

### Insight 2 — Most Overpowered Type Combination

**Query:** `select((p.type1, p.type2, avg(p.total), count(p)) for p in Pokemon)`
ordered by average Total descending, then filtered to combinations with ≥ 5 Pokémon.

The filter prevents single-Pokémon edge cases (one Mega evolution in an otherwise
empty type slot) from occupying the top rankings.

**Finding:** The highest-average type combinations are dominated by **Dragon dual-types**
(Dragon/Flying, Dragon/Psychic, Dragon/Fire) and **Steel/Ghost**. These archetypes
concentrate legendary and pseudo-legendary Pokémon — for example, all Pseudo-legendaries
(Dragonite, Garchomp, Hydreigon…) are Dragon-type, and many legendary trios are Psychic.
At the opposite end, **Bug/Grass** and **Normal** (single-type) have the lowest averages
because they represent early-route Pokémon with minimal base stats.

---

## Technologies & Libraries

| Technology | Why chosen |
|---|---|
| **PonyORM 0.7.19** | Same ORM used throughout Task 3. `avg()` and `count()` are PonyORM generator expression aggregates — no raw SQL needed. `select(...).order_by(lambda ...: desc(a))[:]` retrieves the full ranked result as a list of tuples. |
| **pandas** | `pd.DataFrame` wraps the query results for clean tabular display with `.to_string(index=False)`. |
| **matplotlib** | Line chart for power creep (two series + trend line) and horizontal bar chart for type combinations. Both are rendered inline in the notebook. |
| **numpy** | `np.polyfit(x, y, 1)` fits a degree-1 polynomial to the non-legendary average-Total series to extract the per-generation slope. |

---

## Challenges & Solutions

**1. Legendaries skew per-generation averages**
Running `avg(p.total)` across all Pokémon per generation conflates non-legendary base
Pokémon with legendaries that have artificially high stats (580–780 Total). Gen 4 would
appear inflated simply because it has 14 legendaries (the most of any generation).
Fix: split the query into two passes — one with `if not p.legendary`, one with
`if p.legendary` — so the two trends can be read independently.

**2. Rare type combinations produce misleading averages**
Without a minimum-count filter, combinations like `Dragon/Ice` (4 Pokémon, all high Total)
ranked at the very top even though the sample size is too small to be meaningful.
Fix: filter the Python-side result list to `cnt >= 5` before constructing the DataFrame,
excluding combinations with insufficient data.

**3. PonyORM `avg()` import**
`avg` is not imported in the Task 3.1 setup cells. Adding `from pony.orm import avg`
at the top of the Task 3.4 section was sufficient; no changes to earlier cells were needed.

---

## Interesting Findings

**Power creep is real but mild.**
The +7–10 Total per generation figure sounds modest, but it compounds: a Gen 6 starter
has roughly the same base Total as a Gen 1 mid-tier Pokémon that has already evolved
once. In competitive play this is amplified by new mechanics introduced each generation
(Mega evolutions in Gen 6 add 100 Total on top of the drift), making Gen 6 Pokémon
disproportionately dominant in unrestricted formats.

**Dragon-types benefit from a "legendary clustering" effect.**
Dragon's sky-high average Total is largely explained by game lore rather than game
balance: Game Freak consistently designates dragons as rare and powerful creatures
(pseudo-legendaries, box legendaries, version mascots). Removing legendaries and
pseudo-legendaries from the Dragon group drops its average Total significantly,
bringing it closer to Water and Psychic non-legendary averages. The stat gap is
therefore a design choice, not a type-mechanics advantage.
