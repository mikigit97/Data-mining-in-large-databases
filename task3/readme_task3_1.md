# Task 3.1 — Pokémon Battle Arena: Data Loading & Schema Design

---

## What I Built and How It Works

`task3_pokemon.ipynb` is a reproducible Jupyter notebook that loads the Pokémon dataset
into an SQLite database via **PonyORM** and prepares the full schema required by
Tasks 3.2 (battle game) and 3.3 (cheat codes).

**Pipeline steps:**

1. **DB creation** — `pokemon.db` is deleted and recreated on every run so the notebook
   is fully reproducible.
2. **Schema definition** — three PonyORM entity classes are defined (`Pokemon`,
   `TypeEffectiveness`, `BattleLog`) and mapped to SQLite tables via
   `db.generate_mapping(create_tables=True)`.
3. **Pokémon load** — `Pokemon.csv` (800 rows) is read into a pandas DataFrame, column
   names are renamed to snake_case, `NaN` in `Type 2` is converted to `None`, and rows
   are inserted one by one inside a `db_session`.
4. **Type chart seed** — the full Gen 6 18×18 type-effectiveness matrix (324 rows) is
   computed from a Python `_CHART` dict and inserted into `TypeEffectiveness`. All 324
   ordered pairs are stored — including neutral (1.0) matchups — so the battle app can
   do a single `.get()` lookup without any Python-side fallback logic.
5. **Verification** — PonyORM generator expressions count rows, check legendary count,
   print per-generation breakdowns, and run spot-check queries against the type chart.

---

## Technologies & Libraries

| Technology | Why chosen |
|---|---|
| **PonyORM 0.7.19** | Same ORM used in Task 2. Generator-expression syntax (`select(p for p in Pokemon if ...)`) keeps all DB interaction in one idiomatic style with no raw SQL. `composite_key()` expresses compound PKs cleanly. |
| **pandas** | Used only for `pd.read_csv()` — the fastest and most reliable way to ingest and rename the CSV columns in one step. No pandas DataFrames are persisted to the DB; PonyORM handles all inserts. |
| **SQLite (via PonyORM)** | Zero-configuration embedded DB. The single file `pokemon.db` contains all three tables and is self-contained for the subsequent app and cheat-code tasks. |
| **Python 3.11 (`.venv311`)** | PonyORM 0.7.19 is incompatible with Python 3.14 (`LOAD_FAST_BORROW` opcode); the same `.venv311` from Task 2 is reused. |

---

## Challenges & Solutions

**1. `#` (Pokédex number) is not a valid primary key**
Mega evolutions (e.g. *Mega Charizard X* and *Mega Charizard Y*) share the same Pokédex
number as their base form. Using `#` as PK would cause a uniqueness violation during insert.
Fix: `Name` is used as the primary key — every row in the CSV has a unique display name,
including Mega forms (`"CharizardMega Charizard X"`).

**2. `Optional(str)` rejects `None` by default in PonyORM**
Calling `Pokemon(type2=None, ...)` raised
`ValueError: Attribute Pokemon.type2 cannot be set to None`.
PonyORM maps `Optional(str)` to an empty string `""` in SQLite by default — `NULL` is not
allowed unless explicitly opted in.
Fix: changed the field declaration to `Optional(str, nullable=True)`, which stores SQL
`NULL` for absent values and allows `p.type2 is None` checks in queries.

**3. `legendary` stored as `True` for all 800 Pokémon**
`df['legendary'].map({'True': True, 'False': False})` was applied, but pandas had already
inferred the column as `bool` dtype directly from the CSV (`Legendary` values are bare
`True`/`False`). The map's string keys did not match, so every entry became `NaN`, and
`bool(NaN)` evaluates to `True` — making every Pokémon legendary.
Fix: removed the `.map()` call entirely. Since pandas reads the column as `bool` dtype,
`bool(row['legendary'])` is correct for both `True` and `False` rows. A dtype assertion
was added to the notebook output to make the inferred type explicit.

---

## Interesting Findings

**The dataset contains 65 legendary Pokémon out of 800 entries (8.1%).**
A PonyORM query confirms this: `count(p for p in Pokemon if p.legendary == True)`.
However, the "800" total includes Mega evolutions as separate rows, so the true count of
distinct species is lower. Filtering out names containing "Mega" gives 721 base-form entries,
of which 63 are legendary — 8.7%.

**The three Pokémon tied for the highest base stat total (780) are all Mega/Primal forms:**
Mega Mewtwo X, Mega Mewtwo Y, and Mega Rayquaza. The highest *non-Mega* total is 680
(Mewtwo base form, Kyurem-Black, Kyurem-White, Zygarde-Complete). This illustrates that
Mega Evolution was specifically designed to push stat totals beyond what any base-form
Legendary could achieve.

**Water is the most common primary type (112 Pokémon), followed by Normal (98) and Grass (70).**
At the other extreme, Flying has only 4 Pokémon with it as their primary type (vs. 97 as
a secondary), making it almost exclusively a secondary type — a structural design choice
in the game that is directly visible from the database.
