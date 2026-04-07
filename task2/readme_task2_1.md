# Task 2.1 – Data Modeling with ORM (PonyORM)

## What I Built and How It Works

I loaded **The Oscar Award** dataset (`the_oscar_award.csv`, 11,110 rows, 97 ceremonies,
1927–2024) into a SQLite database using **PonyORM**. The raw CSV is a flat nomination log
where every row represents one person/film nominated in one category at one ceremony.
Rather than storing it flat, I designed a normalised five-entity schema to eliminate
redundancy and make ORM queries expressive.

The notebook (`task2_oscar.ipynb`) follows this sequence:
1. Delete and recreate `oscar.db` for full reproducibility.
2. Define five PonyORM entity classes and call `db.generate_mapping(create_tables=True)`
   to create the SQLite schema.
3. Load the CSV with pandas, then populate entities in dependency order:
   `Ceremony` → `Category` → `Person` → `Film` → `Nomination`.
4. Build in-memory lookup dictionaries for each parent entity so that the 11,110-row
   nomination loop avoids repeated DB round-trips.
5. Run three verification queries to confirm row counts and data integrity.

### Schema

| Entity | PK | Key fields | Notes |
|---|---|---|---|
| `Ceremony` | `number` (int) | `year` | 97 ceremonies, natural PK |
| `Category` | auto int | `name` (unique), `canon_name` | 118 specific → 58 canonical |
| `Person` | auto int | `name` (unique) | 6,893 distinct nominees |
| `Film` | auto int | `title` + `year` (composite unique) | 5,233 unique (title, year) pairs |
| `Nomination` | auto int | FK → all four above + `winner` | Central junction table |

`Nomination.person` and `Nomination.film` are **Optional** to handle the 7 rows with no
named individual (honorary film awards) and 359 early rows with no film attribution
(sound studios, title writers).

---

## Technologies & Libraries

| Technology | Why chosen |
|---|---|
| **PonyORM 0.7.19** | Generator-expression query syntax (`select(n for n in Nomination if n.winner)`) reads like plain Python rather than chained `.filter()` calls. Schema definition via `Required`, `Optional`, and `Set` automatically infers foreign keys and reverse relations, reducing boilerplate compared to SQLAlchemy's explicit `relationship()` + `ForeignKey()` declarations. |
| **pandas** | Used solely for CSV ingestion (`pd.read_csv`) and deduplication (`.drop_duplicates()`) before handing data off to PonyORM entity constructors. |
| **SQLite (via PonyORM)** | Matches the assignment requirement; `db.bind(provider='sqlite', ...)` is PonyORM's one-line binding. |

**Why PonyORM over SQLAlchemy / Peewee:**
SQLAlchemy is the most production-mature choice but requires a `session` object, explicit
`relationship()` declarations on both sides of a relation, and verbose `query()` chains.
Peewee is simpler but less expressive for multi-table aggregations. PonyORM's generator
expressions match the natural way a data analyst thinks about queries and produce clean,
readable code for a homework notebook context.

---

## Challenges & Solutions

**1. PonyORM generator queries incompatible with Python 3.14**
PonyORM translates generator expressions into SQL by decompiling Python bytecode at
runtime. Python 3.14 introduced a new opcode (`LOAD_FAST_BORROW`) that PonyORM 0.7.19's
decompiler does not recognise, raising `DecompileError: Unsupported operation:
LOAD_FAST_BORROW` on any `select(... for ... in ...)` call.
Fix: created a dedicated Python 3.11 virtual environment (`.venv311/`) where PonyORM runs
correctly, registered it as a Jupyter kernel (`oscar-py311`), and set the notebook's
kernel metadata to that kernel. All PonyORM generator expressions run natively on Python
3.11 — no raw SQL workarounds needed.

**2. Composite unique key syntax in PonyORM**
The first draft placed `from pony.orm import composite_key` and the call inside the `Film`
class body as a class attribute assignment. PonyORM expects `composite_key(field1, field2)`
to be called as a bare statement at class scope (not assigned), with `composite_key`
imported at module level.
Fix: moved the import to the top-level import block and called `composite_key(title, year)`
as a bare statement inside the class body.

**3. Database path resolution under nbconvert**
Using `DB_PATH = "oscar.db"` (relative) caused `OperationalError: unable to open database
file` when nbconvert executed the notebook, because nbconvert's kernel working directory
differs from the notebook's directory.
Fix: computed an absolute path with `os.path.dirname(os.path.abspath("task2_oscar.ipynb"))`
so the path is always resolved relative to the notebook file regardless of the launch CWD.

**4. Nullable fields require Optional, not Required**
Seven rows have a null `name` and 359 rows have a null `film`. Declaring these as
`Required` would have caused PonyORM to raise a `ConstraintError` when inserting those
nominations.
Fix: declared `Nomination.person` and `Nomination.film` as `Optional`, and added
`if pd.notna(row['name'])` / `if pd.notna(row['film'])` guards before looking up the
parent entity, passing `None` to the constructor when the field is absent.

---

## Interesting Findings

**Metro-Goldwyn-Mayer is the most "nominated person" in the dataset (68 nominations).**
The `name` column in early ceremonies was used for studios (MGM, Paramount, RKO) in
sound-recording and short-film categories, not for individual people. This reveals an
important data-quality nuance: pre-1940 Oscar nominations were partly institutional rather
than personal, which the flat CSV obscures but the normalised schema makes queryable.

**Walt Disney has 62 nominations — more than any human director or actor.**
Disney was personally nominated in the Short Subject and Documentary categories throughout
the 1930s–1950s before the Academy shifted to crediting producers and studios separately.
His total dwarfs the most-nominated living director (Woody Allen, ~24 nominations).

**118 specific categories collapse into only 58 canonical ones.**
The Academy has renamed, split, and merged categories many times (e.g. "ACTOR" →
"ACTOR IN A LEADING ROLE", B&W and colour Art Direction merged into one). The
`canon_category` field makes cross-era comparisons possible without manually normalising
118 category strings.
