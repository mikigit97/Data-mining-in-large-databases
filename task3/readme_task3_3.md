# Task 3.3 — Pokémon Battle Arena: Cheat Codes

---

## What I Built and How It Works

Five cheat codes were added to `task3/app3.py`. Each code is entered via a
"🔑 Enter Cheat Code" expander at the bottom of the battle screen. Activating a
valid code executes a **real PonyORM write operation** (`UPDATE` or `INSERT`) on
`pokemon.db`, immediately updates the in-memory session-state team so the effect
is visible in the current battle, and records the code in `st.session_state.cheats_used`.

When a battle ends the cheat codes are written to the `BattleLog.cheats_used`
column. The **Results** screen always shows a "🔍 Cheat Audit" section that
queries the DB for anomalous stats and lists all past cheat battles.

| Code | DB operation | Effect |
|---|---|---|
| `UPUPDOWNDOWN` | `UPDATE Pokemon SET hp = hp * 2` for each player Pokémon | Doubles HP in DB and live HP bars |
| `GODMODE` | `UPDATE Pokemon SET defense = 999, sp_def = 999` for the active Pokémon | Makes the active Pokémon nearly invincible to physical and special hits |
| `STEAL` | `INSERT INTO Pokemon` a copy named `"Stolen <name>"` | Adds the AI's highest-Total Pokémon to the player's team |
| `NERF` | `UPDATE Pokemon SET hp/2, attack/2, defense/2, sp_atk/2, sp_def/2, speed/2` for each AI Pokémon | Halves all AI stats both in-game and in the DB |
| `LEGENDARY` | `INSERT INTO Pokemon` a custom `"UltraMewtwo"` (Psychic/Fighting, 780 Total) | Summons an ultra-powerful Pokémon onto the player's team |

**Cheat Audit query** — shown on the Results screen:
- Detects `defense ≥ 999 OR sp_def ≥ 999` → GODMODE evidence
- Detects `hp > 255` (natural dataset max is 255 for Blissey) → UPUPDOWNDOWN evidence
- Detects names matching `"Stolen %"` → STEAL evidence
- Detects `name = "UltraMewtwo"` → LEGENDARY evidence
- Reads `BattleLog.cheats_used IS NOT NULL` → full history of cheat battles with codes and winners

**How to run:**
```
task2/.venv311/Scripts/streamlit run task3/app3.py
```

---

## Technologies & Libraries

| Technology | Why chosen |
|---|---|
| **PonyORM 0.7.19** | Same ORM used throughout Tasks 2–3. `UPDATE` is written via direct attribute assignment inside `@db_session`; `INSERT` uses the entity constructor. Both are real write operations on the SQLite file. |
| **Streamlit** | `st.session_state.cheats_used` (a list) accumulates codes during a battle. `st.rerun()` after each activation refreshes the arena so HP bars and bench panels reflect the change immediately. |
| **Python 3.11 (`.venv311`)** | Same venv as the rest of Task 3. |

---

## Challenges & Solutions

**1. Session-state dict and DB must both be updated**
The battle loop operates entirely on plain Python dicts in `st.session_state`,
not on live PonyORM entities. A DB `UPDATE` alone would have no effect until the
next battle (when stats are reloaded). Fix: each cheat function first writes to
the DB inside a `@db_session` block, then modifies the relevant in-memory dict
fields (`p["defense"] = 999`, etc.) so the change is reflected immediately in
damage calculations and HP bars.

**2. `@st.cache_data` serves stale data after INSERT**
`load_pokemon_list()` is cached with `@st.cache_data`. After `STEAL` or
`LEGENDARY` inserts a new row, the cache still returns the pre-insert snapshot.
Fix: call `load_pokemon_list.clear()` immediately after every `INSERT`, exactly
as `_save_battle_log` calls `load_battle_history.clear()` after writing a
`BattleLog` row.

**3. Duplicate INSERT guard**
If the player activates `STEAL` twice in the same battle, PonyORM would raise an
`IntegrityError` (PrimaryKey violation on `"Stolen <name>"`). Fix: both `_cheat_steal`
and `_cheat_legendary` check `Pokemon.get(name=...)` before inserting, and also
check whether the Pokémon is already in `state["p1_team"]` before appending,
returning an informative message instead of an error.

**4. Initial NERF only halved ATK and SP.ATK — extended to all stats**
The first implementation of `NERF` only halved the AI's `attack` and `sp_atk`,
leaving `defense`, `sp_def`, `hp`, and `speed` untouched. This meant the AI
still took the same number of turns to kill and could still outspeed the player.
Fix: updated `_cheat_nerf` to halve all six base stats (HP, ATK, DEF, SP.ATK,
SP.DEF, Speed) in both the DB and the live session-state dicts. Current HP is
also clamped to the new (halved) max so the HP bar doesn't overflow.

**5. NERF stat anomalies are hard to detect by threshold alone**
After halving, a Pokémon's stats could land anywhere in the natural range —
there is no single threshold that reliably signals "this was NERF'd". Fix: NERF
detection relies on `BattleLog.cheats_used` rather than stat inspection. The
other four cheats produce out-of-range values (defense = 999, hp > 255,
name prefix "Stolen ", name = "UltraMewtwo") that are unambiguously anomalous.

---

## Interesting Findings

**GODMODE + NERF combo is nearly unbeatable.**
Setting the active Pokémon's DEF and SP.DEF to 999 while halving the AI's ATK
and SP.ATK reduces incoming damage to `floor(atk / 999 * 40 * mult) = 0` for
virtually every attacker in the dataset. The only hit that still registers is
from a type-immune chain (0× damage → 0 regardless), which the "has no effect"
message already handles. In practice the player takes 0–1 damage per round and
wins within the AI's HP pool.

**Stolen legendaries are dominant but not invulnerable.**
`STEAL` targeting a Primal Kyogre (Total 770) adds its full base stats to the
player's bench. Primal Kyogre's SP.ATK (180) combined with Water being super
effective against Fire/Rock types results in one-shot damage against common AI
Pokémon. However, type immunity (e.g. Water has no effect on Grass/Dragon types
at 0×) still applies, demonstrating that even cheated stats don't override the
type chart.

**The cheat audit doubles as a post-game DB sanity check.**
After a session with UPUPDOWNDOWN activated, Blissey's HP in the DB reads 510
— clearly above the dataset ceiling of 255. This makes the audit query
(`WHERE hp > 255`) a reliable detector that works across game sessions, not just
the current one.
