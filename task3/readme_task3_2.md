# Task 3.2 — Pokémon Battle Arena: Battle Game

---

## What I Built and How It Works

`task3/app3.py` is a Streamlit app that lets a player assemble a team of 1–3 Pokémon and
battle a randomly-chosen AI opponent in a turn-based arena. All Pokémon stats and type
effectiveness values are read from `pokemon.db` (built in Task 3.1). After each battle the
result is written back to the `BattleLog` table in the same database.

**App flow (three phases):**

1. **Setup** — Player 1 uses a searchable multiselect to pick 1–3 Pokémon from all 800 in
   the database. A live preview shows each Pokémon's stats (HP, ATK, DEF, Speed, Total,
   legendary flag). Clicking "Start Battle!" locks the team and has the AI randomly draft 3
   Pokémon from the remaining pool.

2. **Battle** — A side-by-side layout shows both active Pokémon with HP progress bars and
   bench information. Each click of **Attack!** resolves one full round (both Pokémon attack),
   appends a formatted entry to the running log, and checks for a win condition.

3. **Results** — The winner is announced with a coloured banner (balloons for the player,
   error for the AI). The full turn-by-turn log is available in an expander, one
   `BattleLog` row is written to the DB, and a "Battle History" table shows all past results.

**How to run:**
```
task2/.venv311/Scripts/streamlit run task3/app3.py
```
(run from repo root — DB path is resolved relative to the script file location)

---

## Battle Mechanics

### Turn order
Within each round the faster Pokémon attacks first:
```
first = p1_active if p1_active.speed >= p2_active.speed else p2_active
```
Speed ties are broken in favour of Player 1. If the first attacker knocks out the
defender, the defender cannot counter-attack that round.

### Damage formula
```
type_mult = chart[(attacker.type1, defender.type1)]
if defender.type2:
    type_mult *= chart[(attacker.type1, defender.type2)]
damage = max(1, floor(attacker.attack / defender.defense * 40 * type_mult))
```
- Base power of **40** (equivalent to a standard Gen 1–6 normal-priority move).
- `attacker.attack / defender.defense` scales damage fairly across the stat range.
- `type_mult` is looked up from the `TypeEffectiveness` table for every (attacker type, defender type) pair — all 324 pairs are stored, so the lookup is a single `dict.get()` with no Python-side fallback.
- Dual-type defenders chain both multipliers (e.g. Water vs Fire/Flying Charizard → 2.0 × 1.0 = 2.0×).

### Effectiveness messages
| Multiplier | Message |
|---|---|
| > 1.0 | "It's super effective!" |
| < 1.0 and > 0 | "It's not very effective..." |
| 0.0 | "has no effect" |

### Win condition
A Pokémon faints when its current HP reaches 0. The next non-fainted team member is sent
out automatically. The battle ends when every Pokémon on one side has fainted.

### AI strategy
The AI picks 3 Pokémon at random at the start of each battle (from the pool of Pokémon
not chosen by Player 1). Each round it always attacks — no move selection logic beyond
the shared damage formula. This satisfies the "AI can use random moves" requirement.

---

## Technologies & Libraries

| Technology | Why chosen |
|---|---|
| **PonyORM 0.7.19** | Same ORM used throughout Tasks 2 and 3.1. `@db_session` wraps both read and write operations; inserting a `BattleLog` row after each battle uses PonyORM's entity constructor rather than raw SQL. |
| **Streamlit** | Reuses the same framework as Task 2.2. `st.session_state` stores the full mutable battle state (team HP, active indices, turn log) across button-click reruns. `@st.cache_resource` prevents re-binding the DB on every rerun; `@st.cache_data` caches the 800-Pokémon list and 324-pair type chart as plain dicts. |
| **Python 3.11 (`.venv311`)** | PonyORM 0.7.19 is incompatible with Python 3.14 — same venv as Tasks 2 and 3.1. |
| **pandas** | Used only for `pd.DataFrame` construction fed to `st.dataframe` for the battle history table. |

---

## Challenges & Solutions

**1. `@st.cache_data` cannot pickle PonyORM entity objects**
Returning live ORM entity instances from a cached function raises a pickle error on cache
hit (PonyORM entities hold a DB session reference that cannot be serialised).
Fix: `load_pokemon_list()` and `load_type_chart()` open a `db_session`, extract all
data into plain Python dicts/tuples, and return those. Downstream battle logic operates
entirely on plain dicts — no ORM entities outside of `db_session` blocks.

**2. `@st.cache_resource` + entity classes must live inside the cached function**
Defining entity classes at module level and calling `db.bind()` inside `@st.cache_resource`
causes the same issue seen in Task 2.2: each Streamlit rerun creates fresh entity classes
that are not bound to the cached DB instance.
Fix: all three entity classes (`Pokemon`, `TypeEffectiveness`, `BattleLog`), `db.bind()`,
and `db.generate_mapping()` are defined inside `_init_db()` and cached together.
Module-level code calls `_init_db()` each time but only the first call actually binds.

**3. DB path must be absolute to work regardless of working directory**
Running `streamlit run task3/app3.py` from any directory caused a `FileNotFoundError`
for `pokemon.db` when a relative path was used.
Fix: `DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pokemon.db")`
resolves the path relative to the script file, not the current working directory.

**4. Battle history cache stale after write**
After writing a new `BattleLog` row, the `load_battle_history()` cached function still
returns the old list.
Fix: call `load_battle_history.clear()` immediately after `BattleLog(...)` is inserted,
forcing a fresh DB read on the next render.

---

## Interesting Findings

**Speed stat is the single biggest predictor of battle outcome in a 1v1 match.**
Charizard (Speed 100) vs Squirtle (Speed 43): despite Water being super-effective against
Charizard's Fire/Flying typing, Charizard fires twice before Squirtle can land a second
hit — winning in 2 rounds. The asymmetry shows that raw speed advantage can override a
2× type disadvantage when the opponent's HP is low.

**The immune matchup (0× multiplier) creates asymmetric battles.**
Normal-type Pokémon are completely immune to Ghost-type moves (`Normal vs Ghost: 0.0`).
If a player picks a Normal-type against an AI Ghost-type, the AI deals 0 damage every
round while the player chips away freely. The "has no effect" message in the battle log
makes this immediately visible and educates the player about the type chart.

**Legendary Pokémon dominate in Total stats (540–780) but are available in team selection.**
Including legendaries (65 out of 800 rows) in the team pool lets a player build a
deliberately unfair team. Mega Rayquaza (Total 780, Attack 180) calculates to roughly 4–6×
the damage of an average Pokémon before type multipliers — making it a near-guaranteed
win unless the opponent is immune. This mirrors how competitive Pokémon games ban legendaries
from standard play.
