"""
Task 3.2 — Pokémon Battle Arena (Visual Edition)
Run from repo root: task2/.venv311/Scripts/streamlit run task3/app3.py
"""

import math
import os
import random
from datetime import datetime

import streamlit as st
from pony.orm import (
    Database, Optional, PrimaryKey, Required,
    composite_key, db_session, select,
)

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
_HERE   = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_HERE, "pokemon.db")

SPRITE_FRONT = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{}.png"
SPRITE_BACK  = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/{}.png"

TYPE_COLOR = {
    "Normal":   "#A8A878", "Fire":     "#F08030", "Water":   "#6890F0",
    "Grass":    "#78C850", "Electric": "#F8D030", "Ice":     "#98D8D8",
    "Fighting": "#C03028", "Poison":   "#A040A0", "Ground":  "#E0C068",
    "Flying":   "#A890F0", "Psychic":  "#F85888", "Bug":     "#A8B820",
    "Rock":     "#B8A038", "Ghost":    "#705898", "Dragon":  "#7038F8",
    "Dark":     "#705848", "Steel":    "#B8B8D0", "Fairy":   "#EE99AC",
}

CHEAT_CODES = {
    "UPUPDOWNDOWN": "upup",
    "GODMODE":      "godmode",
    "STEAL":        "steal",
    "NERF":         "nerf",
    "LEGENDARY":    "legendary",
}

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

/* ── Keyframes ── */
@keyframes shake {
  0%,100%{transform:translateX(0)}
  20%{transform:translateX(-8px) rotate(-4deg)}
  40%{transform:translateX(8px)  rotate(4deg)}
  60%{transform:translateX(-8px) rotate(-4deg)}
  80%{transform:translateX(8px)  rotate(4deg)}
}
@keyframes dash-right {
  0%  {transform:translateX(0) scaleX(1)}
  45% {transform:translateX(55px) scaleX(0.85)}
  100%{transform:translateX(0) scaleX(1)}
}
@keyframes dash-left {
  0%  {transform:translateX(0) scaleX(-1)}
  45% {transform:translateX(-55px) scaleX(-0.85)}
  100%{transform:translateX(0) scaleX(-1)}
}
@keyframes white-flash {
  0%,100%{filter:brightness(1) saturate(1)}
  25%{filter:brightness(5) saturate(0)}
  50%{filter:brightness(1)}
  75%{filter:brightness(5) saturate(0)}
}
@keyframes gold-flash {
  0%,100%{filter:brightness(1) sepia(0);transform:scale(1)}
  30%{filter:brightness(2.5) sepia(1) hue-rotate(-20deg);transform:scale(1.1)}
  60%{filter:brightness(1);transform:scale(1)}
}
@keyframes faint-drop {
  0%  {transform:translateY(0) rotate(0);opacity:1;filter:grayscale(0)}
  60% {transform:translateY(15px) rotate(-20deg);opacity:.6;filter:grayscale(.6)}
  100%{transform:translateY(70px) rotate(-90deg);opacity:0;filter:grayscale(1)}
}
@keyframes bob {
  0%,100%{transform:translateY(0)}
  50%{transform:translateY(-8px)}
}
@keyframes hp-low-pulse {
  0%,100%{opacity:1}
  50%{opacity:.4}
}
@keyframes slide-in {
  from{transform:translateX(-16px);opacity:0}
  to  {transform:translateX(0);opacity:1}
}
@keyframes winner-glow {
  0%,100%{box-shadow:0 0 12px #FFD700}
  50%{box-shadow:0 0 45px #FFD700,0 0 90px #FF8C00}
}

/* ── Arena ── */
.battle-arena {
  background: linear-gradient(180deg,
    #1a6090 0%, #2980b9 28%, #5dade2 44%,
    #b8956a 55%, #8b6340 58%,
    #4a7c29 62%, #2d5a1b 100%);
  border-radius:14px;
  border:4px solid #111;
  padding:16px 20px 12px;
  position:relative;
  min-height:440px;
  max-width:900px;
  margin:0 auto;
  overflow:hidden;
  box-shadow:0 8px 32px rgba(0,0,0,.65);
}
/* shadows are now children of their sprite wrapper — no longer absolute */
.shadow-ai {
  width:110px;height:14px;
  background:radial-gradient(ellipse,rgba(0,0,0,.35) 50%,transparent 100%);
  border-radius:50%;
  margin-top:-2px;
}
.shadow-p1 {
  width:130px;height:18px;
  background:radial-gradient(ellipse,rgba(0,0,0,.4) 50%,transparent 100%);
  border-radius:50%;
  margin-top:-2px;
}

/* ── HP box ── */
.hp-box {
  background:rgba(0,0,0,.78);
  border:2px solid #555;
  border-radius:8px;
  padding:8px 12px;
  color:#fff;
  min-width:190px;
  max-width:220px;
  position:relative;
}
/* Chat-bubble tails */
.hp-box-ai::before{
  content:'';position:absolute;top:22px;right:-18px;width:0;height:0;
  border-top:9px solid transparent;border-bottom:9px solid transparent;
  border-left:18px solid #555;
}
.hp-box-ai::after{
  content:'';position:absolute;top:24px;right:-14px;width:0;height:0;
  border-top:7px solid transparent;border-bottom:7px solid transparent;
  border-left:14px solid rgba(0,0,0,.78);
}
.hp-box-p1::before{
  content:'';position:absolute;top:22px;left:-18px;width:0;height:0;
  border-top:9px solid transparent;border-bottom:9px solid transparent;
  border-right:18px solid #555;
}
.hp-box-p1::after{
  content:'';position:absolute;top:24px;left:-14px;width:0;height:0;
  border-top:7px solid transparent;border-bottom:7px solid transparent;
  border-right:14px solid rgba(0,0,0,.78);
}
.hp-name{font-weight:700;font-size:13px;margin-bottom:3px;}
.hp-types{margin-bottom:5px;}
.type-badge{
  display:inline-block;padding:1px 7px;border-radius:10px;
  font-size:10px;font-weight:700;color:#fff;margin:1px;
  text-shadow:0 1px 2px rgba(0,0,0,.5);
}
.hp-label{font-size:9px;color:#aaa;text-transform:uppercase;letter-spacing:1px;}
.hp-track{background:#333;border-radius:4px;height:10px;margin:3px 0;overflow:hidden;}
.hp-fill{height:100%;border-radius:4px;transition:width .5s ease,background .5s ease;}
.hp-text{font-size:11px;color:#ccc;text-align:right;}
.hp-low .hp-fill{animation:hp-low-pulse .8s ease-in-out infinite;}

/* ── Sprites ── */
.sprite-wrap{display:inline-block;line-height:0;}
.sprite-ai{
  width:140px;height:140px;object-fit:contain;
  image-rendering:pixelated;image-rendering:crisp-edges;
  transform:scaleX(-1);
}
.sprite-p1{
  width:160px;height:160px;object-fit:contain;
  image-rendering:pixelated;image-rendering:crisp-edges;
}
.fainted-img{filter:grayscale(1) brightness(.5);opacity:.3;}

/* Animation triggers applied to the arena div */
.ev-p1-atk   .sprite-wrap-p1 {animation:dash-right .45s ease-in-out;}
.ev-ai-atk   .sprite-wrap-ai {animation:dash-left  .45s ease-in-out;}
.ev-ai-hit   .sprite-wrap-ai {animation:shake      .55s ease-in-out;}
.ev-p1-hit   .sprite-wrap-p1 {animation:shake      .55s ease-in-out;}
.ev-ai-super .sprite-wrap-ai {animation:gold-flash  .6s ease-in-out;}
.ev-p1-super .sprite-wrap-p1 {animation:gold-flash  .6s ease-in-out;}
.ev-ai-white .sprite-wrap-ai {animation:white-flash .6s ease-in-out;}
.ev-p1-white .sprite-wrap-p1 {animation:white-flash .6s ease-in-out;}
.ev-ai-faint .sprite-wrap-ai .sprite-ai {animation:faint-drop .8s ease-in-out forwards;}
.ev-p1-faint .sprite-wrap-p1 .sprite-p1 {animation:faint-drop .8s ease-in-out forwards;}
.ev-idle     .sprite-wrap-ai {animation:bob 2.8s ease-in-out infinite;}
.ev-idle     .sprite-wrap-p1 {animation:bob 2.5s ease-in-out infinite;}

/* ── Message box (retro Game Boy style) ── */
.msg-box{
  background:#f8f0d8;
  border:3px solid #333;
  border-radius:8px;
  padding:12px 16px;
  font-family:'Courier New',monospace;
  font-size:13px;
  line-height:1.8;
  color:#222;
  min-height:72px;
  margin:8px 0 0;
  animation:slide-in .25s ease-out;
}
.msg-super {color:#b8580a;font-weight:700;}
.msg-not   {color:#666;}
.msg-immune{color:#888;font-style:italic;}
.msg-faint {color:#c0392b;font-weight:700;}
.msg-switch{color:#2471a3;font-weight:700;}

/* ── Log history entries ── */
.log-entry{
  background:#1a1a2e;
  border:1px solid #2c3e6e;
  border-radius:6px;
  padding:8px 12px;
  margin:4px 0;
  font-size:12px;
  color:#ccc;
  line-height:1.7;
  animation:slide-in .3s ease-out;
}
.log-round-title{color:#7f8cff;font-weight:700;}

/* ── Setup card ── */
.poke-card{
  background:linear-gradient(135deg,#1a1a2e,#16213e);
  border:2px solid #0f3460;
  border-radius:12px;
  padding:14px 10px;
  text-align:center;
  color:#fff;
  transition:transform .2s,border-color .2s;
}
.poke-card:hover{transform:translateY(-4px);border-color:#e94560;}
.poke-card img{width:96px;height:96px;image-rendering:pixelated;}
.poke-card .pname{font-weight:700;font-size:13px;margin:6px 0 3px;}
.poke-card .pstats{font-size:10px;color:#aaa;line-height:1.6;}
.legendary-star{color:#FFD700;}

/* ── Winner banner ── */
.winner-banner{
  background:linear-gradient(135deg,#1a1a2e,#2c3e6e);
  border:3px solid #FFD700;
  border-radius:14px;
  padding:24px;text-align:center;
  animation:winner-glow 1.5s ease-in-out infinite;
  color:#FFD700;font-size:28px;font-weight:900;
  margin:20px 0;
}

/* ── History table ── */
.hist-table{width:100%;border-collapse:collapse;font-size:12px;}
.hist-table th{
  background:#1a1a2e;color:#7f8cff;
  padding:8px;text-align:left;border-bottom:2px solid #2c3e6e;
}
.hist-table td{padding:7px 8px;border-bottom:1px solid #2c3e6e;color:#ccc;}
.hist-table tr:nth-child(even) td{background:rgba(255,255,255,.03);}

/* ── Cheat codes ── */
.cheat-banner{
  background:linear-gradient(90deg,#7b0000,#c0392b);
  border:2px solid #FFD700;border-radius:8px;
  color:#FFD700;font-weight:700;font-size:13px;
  padding:8px 14px;margin:8px 0;text-align:center;
  animation:winner-glow .8s ease-in-out 2;
}
.cheat-tag{
  display:inline-block;background:#7b0000;color:#FFD700;
  border:1px solid #FFD700;border-radius:12px;
  padding:2px 10px;font-size:11px;font-weight:700;margin:2px;
}
</style>
"""

# ---------------------------------------------------------------------------
# DB init
# ---------------------------------------------------------------------------
@st.cache_resource
def _init_db():
    db = Database()

    class Pokemon(db.Entity):
        name           = PrimaryKey(str)
        pokedex_number = Required(int)
        type1          = Required(str)
        type2          = Optional(str, nullable=True)
        total          = Required(int)
        hp             = Required(int)
        attack         = Required(int)
        defense        = Required(int)
        sp_atk         = Required(int)
        sp_def         = Required(int)
        speed          = Required(int)
        generation     = Required(int)
        legendary      = Required(bool)

    class TypeEffectiveness(db.Entity):
        attacker_type = Required(str)
        defender_type = Required(str)
        multiplier    = Required(float)
        composite_key(attacker_type, defender_type)

    class BattleLog(db.Entity):
        id          = PrimaryKey(int, auto=True)
        timestamp   = Required(str)
        p1_pokemon  = Required(str)
        p2_pokemon  = Required(str)
        winner      = Required(str)
        turns       = Required(int)
        cheats_used = Optional(str, nullable=True)

    db.bind(provider="sqlite", filename=DB_PATH, create_db=False)
    db.generate_mapping(create_tables=False)
    return db, Pokemon, TypeEffectiveness, BattleLog


@st.cache_data
def load_pokemon_list() -> list[dict]:
    _, Pokemon, _, _ = _init_db()
    with db_session:
        rows = select(p for p in Pokemon).order_by(lambda p: p.name)[:]
        return [
            {"name": p.name, "pokedex_number": p.pokedex_number,
             "type1": p.type1, "type2": p.type2,
             "hp": p.hp, "attack": p.attack, "defense": p.defense,
             "sp_atk": p.sp_atk, "sp_def": p.sp_def, "speed": p.speed,
             "total": p.total, "legendary": p.legendary,
             "generation": p.generation}
            for p in rows
        ]


@st.cache_data
def load_type_chart() -> dict:
    _, _, TypeEffectiveness, _ = _init_db()
    with db_session:
        rows = select(t for t in TypeEffectiveness)[:]
        return {(t.attacker_type, t.defender_type): t.multiplier for t in rows}


@st.cache_data
def load_battle_history() -> list[dict]:
    _, _, _, BattleLog = _init_db()
    with db_session:
        rows = select(b for b in BattleLog).order_by(lambda b: b.id).fetch()[::-1]
        return [{"id": b.id, "timestamp": b.timestamp,
                 "p1_team": b.p1_pokemon, "p2_team": b.p2_pokemon,
                 "winner": b.winner, "turns": b.turns}
                for b in rows]


# ---------------------------------------------------------------------------
# Battle logic
# ---------------------------------------------------------------------------
def _make_combatant(poke: dict) -> dict:
    return {**poke, "current_hp": poke["hp"], "fainted": False}


def _next_alive(team, idx):
    for i in range(idx + 1, len(team)):
        if not team[i]["fainted"]:
            return i
    return None


def _all_fainted(team) -> bool:
    return all(p["fainted"] for p in team)


def _calc_damage(attacker, defender, chart, attack_type: str = "physical"):
    mult = chart.get((attacker["type1"], defender["type1"]), 1.0)
    if defender["type2"]:
        mult *= chart.get((attacker["type1"], defender["type2"]), 1.0)
    if attack_type == "special":
        atk_val, def_val = attacker["sp_atk"], defender["sp_def"]
    else:
        atk_val, def_val = attacker["attack"], defender["defense"]
    return max(1, math.floor(atk_val / def_val * 40 * mult)), mult


def _ai_attack_type(attacker: dict, defender: dict) -> str:
    """AI picks whichever attack category deals more damage to this defender."""
    phys = attacker["attack"] / max(1, defender["defense"])
    spec = attacker["sp_atk"] / max(1, defender["sp_def"])
    return "special" if spec > phys else "physical"


def _do_round(state: dict, chart: dict, p1_action: str = "physical") -> dict:
    p1 = state["p1_team"][state["p1_idx"]]
    p2 = state["p2_team"][state["p2_idx"]]
    state["turn"] += 1

    ai_action = _ai_attack_type(p2, p1)

    ev = {
        "p1_attacked": False, "ai_attacked": False,
        "p1_hit": False,      "ai_hit": False,
        "p1_super": False,    "ai_super": False,
        "p1_immune": False,   "ai_immune": False,
        "p1_fainted": False,  "ai_fainted": False,
        "p1_switched": False, "ai_switched": False,
    }

    first, second = (p1, p2) if p1["speed"] >= p2["speed"] else (p2, p1)
    first_is_p1   = (first is p1)
    first_action  = p1_action if first_is_p1 else ai_action
    second_action = p1_action if not first_is_p1 else ai_action
    log_lines     = [f"<span class='log-round-title'>— Round {state['turn']} —</span>"]

    def _attack(attacker, defender, atk_is_p1: bool, attack_type: str = "physical"):
        dmg, mult = _calc_damage(attacker, defender, chart, attack_type)
        atk_pos = "Your" if atk_is_p1 else "AI's"
        def_pos = "AI's" if atk_is_p1 else "Your"
        sp_label = " <span style='color:#a78bfa'>(Special)</span>" if attack_type == "special" else ""

        if atk_is_p1:
            ev["p1_attacked"] = True
        else:
            ev["ai_attacked"] = True

        if mult == 0:
            log_lines.append(
                f"<span class='msg-immune'>{atk_pos} <b>{attacker['name']}</b>{sp_label} attacks "
                f"{def_pos} <b>{defender['name']}</b> — has no effect!</span>"
            )
            if atk_is_p1:
                ev["ai_immune"] = True
            else:
                ev["p1_immune"] = True
            return

        defender["current_hp"] = max(0, defender["current_hp"] - dmg)

        if atk_is_p1:
            ev["ai_hit"] = True
            if mult > 1.0:
                ev["ai_super"] = True
        else:
            ev["p1_hit"] = True
            if mult > 1.0:
                ev["p1_super"] = True

        eff_html = ""
        if mult > 1.0:
            eff_html = " <span class='msg-super'>It's super effective!</span>"
        elif mult < 1.0:
            eff_html = " <span class='msg-not'>It's not very effective…</span>"

        log_lines.append(
            f"{atk_pos} <b>{attacker['name']}</b>{sp_label} dealt "
            f"<b>{dmg} damage</b> to {def_pos} <b>{defender['name']}</b>.{eff_html}"
        )

        if defender["current_hp"] == 0:
            defender["fainted"] = True
            faint_key = "ai_fainted" if atk_is_p1 else "p1_fainted"
            ev[faint_key] = True
            log_lines.append(
                f"<span class='msg-faint'>{def_pos} <b>{defender['name']}</b> fainted!</span>"
            )

    _attack(first, second, first_is_p1, first_action)
    if not second["fainted"]:
        _attack(second, first, not first_is_p1, second_action)

    if state["p1_team"][state["p1_idx"]]["fainted"]:
        nxt = _next_alive(state["p1_team"], state["p1_idx"])
        if nxt is not None:
            state["p1_idx"] = nxt
            ev["p1_switched"] = True   # new sprite → skip faint animation on it
            log_lines.append(
                f"<span class='msg-switch'>You send out <b>{state['p1_team'][nxt]['name']}</b>!</span>"
            )
    if state["p2_team"][state["p2_idx"]]["fainted"]:
        nxt = _next_alive(state["p2_team"], state["p2_idx"])
        if nxt is not None:
            state["p2_idx"] = nxt
            ev["ai_switched"] = True   # new sprite → skip faint animation on it
            log_lines.append(
                f"<span class='msg-switch'>AI sends out <b>{state['p2_team'][nxt]['name']}</b>!</span>"
            )

    if _all_fainted(state["p1_team"]):
        state["winner"] = "Player 2 (AI)"
    elif _all_fainted(state["p2_team"]):
        state["winner"] = "Player 1"

    state["last_events"] = ev
    state["log"].insert(0, "<br>".join(log_lines))
    return state


def _do_switch_turn(state: dict, chart: dict, new_p1_idx: int) -> dict:
    """Player voluntarily switches Pokémon — uses their turn, AI still attacks."""
    old_name = state["p1_team"][state["p1_idx"]]["name"]
    state["p1_idx"] = new_p1_idx
    new_poke = state["p1_team"][new_p1_idx]
    state["turn"] += 1

    ev = {
        "p1_attacked": False, "ai_attacked": True,
        "p1_hit": False,      "ai_hit": False,
        "p1_super": False,    "ai_super": False,
        "p1_immune": False,   "ai_immune": False,
        "p1_fainted": False,  "ai_fainted": False,
        "p1_switched": True,  "ai_switched": False,
    }

    log_lines = [f"<span class='log-round-title'>— Round {state['turn']} —</span>"]
    log_lines.append(
        f"<span class='msg-switch'>You withdrew <b>{old_name}</b> "
        f"and sent out <b>{new_poke['name']}</b>!</span>"
    )

    # AI attacks the incoming Pokémon
    p2 = state["p2_team"][state["p2_idx"]]
    ai_type = _ai_attack_type(p2, new_poke)
    sp_label = " <span style='color:#a78bfa'>(Special)</span>" if ai_type == "special" else ""
    dmg, mult = _calc_damage(p2, new_poke, chart, ai_type)

    if mult == 0:
        log_lines.append(
            f"<span class='msg-immune'>AI's <b>{p2['name']}</b>{sp_label} attacks "
            f"Your <b>{new_poke['name']}</b> — has no effect!</span>"
        )
        ev["p1_immune"] = True
    else:
        new_poke["current_hp"] = max(0, new_poke["current_hp"] - dmg)
        ev["p1_hit"] = True
        if mult > 1.0:
            ev["p1_super"] = True
        eff_html = ""
        if mult > 1.0:
            eff_html = " <span class='msg-super'>It's super effective!</span>"
        elif mult < 1.0:
            eff_html = " <span class='msg-not'>It's not very effective…</span>"
        log_lines.append(
            f"AI's <b>{p2['name']}</b>{sp_label} dealt <b>{dmg} damage</b> "
            f"to Your <b>{new_poke['name']}</b>.{eff_html}"
        )
        if new_poke["current_hp"] == 0:
            new_poke["fainted"] = True
            ev["p1_fainted"] = True
            log_lines.append(
                f"<span class='msg-faint'>Your <b>{new_poke['name']}</b> fainted!</span>"
            )
            nxt = _next_alive(state["p1_team"], new_p1_idx)
            if nxt is not None:
                state["p1_idx"] = nxt
                ev["p1_switched"] = True
                log_lines.append(
                    f"<span class='msg-switch'>You send out "
                    f"<b>{state['p1_team'][nxt]['name']}</b>!</span>"
                )

    if _all_fainted(state["p1_team"]):
        state["winner"] = "Player 2 (AI)"
    elif _all_fainted(state["p2_team"]):
        state["winner"] = "Player 1"

    state["last_events"] = ev
    state["log"].insert(0, "<br>".join(log_lines))
    return state


def _save_battle_log(state: dict):
    _, _, _, BattleLog = _init_db()
    cheats = state.get("cheats_used") or []
    with db_session:
        BattleLog(
            timestamp   = datetime.now().isoformat(timespec="seconds"),
            p1_pokemon  = ", ".join(p["name"] for p in state["p1_team"]),
            p2_pokemon  = ", ".join(p["name"] for p in state["p2_team"]),
            winner      = state["winner"],
            turns       = state["turn"],
            cheats_used = ", ".join(cheats) if cheats else None,
        )
    load_battle_history.clear()


# ---------------------------------------------------------------------------
# Cheat system
# ---------------------------------------------------------------------------
def _purge_cheat_db(state=None):
    """Delete/restore all DB changes made by cheats.
    state is st.session_state (or a plain dict); pass it to restore NERF originals
    which can't be detected by threshold alone."""
    _, Pokemon, _, _ = _init_db()
    with db_session:
        # Restore NERF'd stats from stored originals (undetectable otherwise)
        for name, orig in ((state or {}).get("cheat_nerf_originals") or {}).items():
            row = Pokemon.get(name=name)
            if row:
                for attr, val in orig.items():
                    setattr(row, attr, val)
        # Delete rows inserted by STEAL / LEGENDARY
        for row in select(p for p in Pokemon
                          if p.name.startswith("Stolen ") or p.name == "UltraMewtwo")[:]:
            row.delete()
        # Reset GODMODE (defense/sp_def ≥ 999)
        for row in select(p for p in Pokemon
                          if p.defense >= 999 or p.sp_def >= 999)[:]:
            if row.defense >= 999:
                row.defense = 250
            if row.sp_def >= 999:
                row.sp_def = 250
        # Reset UPUPDOWNDOWN (hp > 255 = above natural dataset max)
        for row in select(p for p in Pokemon if p.hp > 255)[:]:
            row.hp = row.hp // 2
    load_pokemon_list.clear()


def _cheat_upup(state) -> str:
    """UPUPDOWNDOWN — double HP of all player Pokémon (UPDATE)."""
    _, Pokemon, _, _ = _init_db()
    with db_session:
        for p in state["p1_team"]:
            row = Pokemon.get(name=p["name"])
            if row:
                row.hp = row.hp * 2
    for p in state["p1_team"]:
        p["hp"]         = p["hp"] * 2
        p["current_hp"] = min(p["current_hp"] * 2, p["hp"])
    return "UPUPDOWNDOWN activated! All your Pokémon HP doubled!"


def _cheat_godmode(state) -> str:
    """GODMODE — set active Pokémon's DEF & SP.DEF to 999 (UPDATE)."""
    _, Pokemon, _, _ = _init_db()
    active = state["p1_team"][state["p1_idx"]]
    with db_session:
        row = Pokemon.get(name=active["name"])
        if row:
            row.defense = 999
            row.sp_def  = 999
    active["defense"] = 999
    active["sp_def"]  = 999
    return f"GODMODE activated! {active['name']}'s DEF & SP.DEF set to 999!"


def _cheat_steal(state) -> str:
    """STEAL — copy AI's strongest Pokémon to player team (INSERT)."""
    _, Pokemon, _, _ = _init_db()
    strongest   = max(state["p2_team"], key=lambda p: p["total"])
    stolen_name = "Stolen " + strongest["name"]
    if any(p["name"] == stolen_name for p in state["p1_team"]):
        return f"STEAL: {stolen_name} is already on your team!"
    with db_session:
        if not Pokemon.get(name=stolen_name):
            Pokemon(
                name           = stolen_name,
                pokedex_number = strongest["pokedex_number"],
                type1          = strongest["type1"],
                type2          = strongest.get("type2"),
                total          = strongest["total"],
                hp             = strongest["hp"],
                attack         = strongest["attack"],
                defense        = strongest["defense"],
                sp_atk         = strongest["sp_atk"],
                sp_def         = strongest["sp_def"],
                speed          = strongest["speed"],
                generation     = strongest.get("generation", 1),
                legendary      = strongest["legendary"],
            )
    load_pokemon_list.clear()
    state["p1_team"].append(_make_combatant({**strongest, "name": stolen_name}))
    return f"STEAL activated! {stolen_name} joins your team!"


def _cheat_nerf(state) -> str:
    """NERF — halve ALL stats of the AI team (UPDATE)."""
    _, Pokemon, _, _ = _init_db()
    originals = state.get("cheat_nerf_originals") or {}
    with db_session:
        for p in state["p2_team"]:
            row = Pokemon.get(name=p["name"])
            if row:
                # Save originals before modifying (only on first NERF)
                if p["name"] not in originals:
                    originals[p["name"]] = {
                        "hp": row.hp, "attack": row.attack, "defense": row.defense,
                        "sp_atk": row.sp_atk, "sp_def": row.sp_def, "speed": row.speed,
                    }
                row.hp      = max(1, row.hp      // 2)
                row.attack  = max(1, row.attack  // 2)
                row.defense = max(1, row.defense // 2)
                row.sp_atk  = max(1, row.sp_atk  // 2)
                row.sp_def  = max(1, row.sp_def  // 2)
                row.speed   = max(1, row.speed   // 2)
    state["cheat_nerf_originals"] = originals
    for p in state["p2_team"]:
        new_hp       = max(1, p["hp"]      // 2)
        p["attack"]  = max(1, p["attack"]  // 2)
        p["defense"] = max(1, p["defense"] // 2)
        p["sp_atk"]  = max(1, p["sp_atk"]  // 2)
        p["sp_def"]  = max(1, p["sp_def"]  // 2)
        p["speed"]   = max(1, p["speed"]   // 2)
        p["current_hp"] = max(1, min(p["current_hp"], new_hp))
        p["hp"] = new_hp
    return "NERF activated! All AI team stats halved!"


def _cheat_legendary(state) -> str:
    """LEGENDARY — insert custom ultra-powerful Pokémon and add to team (INSERT)."""
    _, Pokemon, _, _ = _init_db()
    ultra_name = "UltraMewtwo"
    if any(p["name"] == ultra_name for p in state["p1_team"]):
        return f"LEGENDARY: {ultra_name} is already on your team!"
    with db_session:
        if not Pokemon.get(name=ultra_name):
            Pokemon(
                name           = ultra_name,
                pokedex_number = 150,
                type1          = "Psychic",
                type2          = "Fighting",
                total          = 780,
                hp             = 130,
                attack         = 190,
                defense        = 120,
                sp_atk         = 220,
                sp_def         = 120,
                speed          = 140,
                generation     = 1,
                legendary      = True,
            )
    load_pokemon_list.clear()
    ultra = {
        "name": ultra_name, "pokedex_number": 150,
        "type1": "Psychic", "type2": "Fighting",
        "total": 780, "hp": 130, "attack": 190, "defense": 120,
        "sp_atk": 220, "sp_def": 120, "speed": 140,
        "generation": 1, "legendary": True,
    }
    state["p1_team"].append(_make_combatant(ultra))
    return f"LEGENDARY activated! {ultra_name} joins your team!"


def _apply_cheat(code: str, state) -> str | None:
    """Dispatch cheat code. Returns a message string or None if unrecognised."""
    key = CHEAT_CODES.get(code.strip().upper())
    if key == "upup":      return _cheat_upup(state)
    if key == "godmode":   return _cheat_godmode(state)
    if key == "steal":     return _cheat_steal(state)
    if key == "nerf":      return _cheat_nerf(state)
    if key == "legendary": return _cheat_legendary(state)
    return None


def _run_cheat_audit(cheats_used: list) -> list[str]:
    """Query DB for stat anomalies, plus session-state cheats that leave no DB trace."""
    _, Pokemon, _, _ = _init_db()
    findings = []
    with db_session:
        godmode  = select(p.name for p in Pokemon
                          if p.defense >= 999 or p.sp_def >= 999)[:]
        hp_boost = select((p.name, p.hp) for p in Pokemon if p.hp > 255)[:]
        stolen   = select(p.name for p in Pokemon
                          if p.name.startswith("Stolen "))[:]
        ultra    = select(p.name for p in Pokemon
                          if p.name == "UltraMewtwo")[:]
    if godmode:
        findings.append(f"**GODMODE** — DEF/SP.DEF ≥ 999 detected on: "
                        + ", ".join(f"`{n}`" for n in godmode))
    if hp_boost:
        findings.append(f"**UPUPDOWNDOWN** — HP > 255 (natural max) detected on: "
                        + ", ".join(f"`{n}` (HP={hp})" for n, hp in hp_boost))
    if stolen:
        findings.append(f"**STEAL** — stolen Pokémon in DB: "
                        + ", ".join(f"`{n}`" for n in stolen))
    if ultra:
        findings.append("**LEGENDARY** — `UltraMewtwo` exists in DB")
    # NERF halves stats into the natural range so it's undetectable by DB query alone
    if "NERF" in cheats_used:
        findings.append("**NERF** — all AI stats halved")
    return findings


# ---------------------------------------------------------------------------
# Visual helpers
# ---------------------------------------------------------------------------
def _type_badge(t: str) -> str:
    c = TYPE_COLOR.get(t, "#888")
    return f'<span class="type-badge" style="background:{c}">{t}</span>'


def _hp_bar_html(poke: dict, side: str = "") -> str:
    cur, mx = poke["current_hp"], poke["hp"]
    ratio   = cur / mx if mx else 0
    pct     = ratio * 100
    color   = "#2ecc71" if ratio > 0.5 else ("#f39c12" if ratio > 0.25 else "#e74c3c")
    low_cls = "hp-low" if ratio <= 0.25 else ""
    badges  = _type_badge(poke["type1"]) + (_type_badge(poke["type2"]) if poke["type2"] else "")
    leg     = ' <span class="legendary-star">★</span>' if poke.get("legendary") else ""
    side_cls = f" hp-box-{side}" if side else ""
    return f"""
<div class="hp-box{side_cls} {low_cls}">
  <div class="hp-name">{poke['name']}{leg}</div>
  <div class="hp-types">{badges}</div>
  <div class="hp-label">HP</div>
  <div class="hp-track">
    <div class="hp-fill" style="width:{pct:.1f}%;background:{color}"></div>
  </div>
  <div class="hp-text">{cur} / {mx}</div>
</div>"""


def _sprite_html(poke: dict, is_player: bool) -> str:
    pid   = poke["pokedex_number"]
    url   = SPRITE_BACK.format(pid) if is_player else SPRITE_FRONT.format(pid)
    fb    = SPRITE_FRONT.format(pid)
    cls   = "sprite-p1" if is_player else "sprite-ai"
    wrap  = "sprite-wrap-p1" if is_player else "sprite-wrap-ai"
    faded = "fainted-img" if poke["fainted"] else ""
    return (f'<div class="sprite-wrap {wrap}">'
            f'<img src="{url}" class="{cls} {faded}" onerror="this.src=\'{fb}\'">'
            f'</div>')


def _arena_ev_classes(ev: dict | None) -> str:
    if ev is None:
        return "ev-idle"
    cls = []
    if ev.get("p1_attacked"):  cls.append("ev-p1-atk")
    if ev.get("ai_attacked"):  cls.append("ev-ai-atk")
    # Only play faint animation when NO switch happened (sprite still shows the fainted Pokémon).
    # If a switch occurred, the incoming Pokémon is already in the slot — skip faint on it.
    if ev.get("ai_fainted") and not ev.get("ai_switched"):
        cls.append("ev-ai-faint")
    elif ev.get("ai_super"):   cls.append("ev-ai-super")
    elif ev.get("ai_hit"):     cls.append("ev-ai-white")
    if ev.get("p1_fainted") and not ev.get("p1_switched"):
        cls.append("ev-p1-faint")
    elif ev.get("p1_super"):   cls.append("ev-p1-super")
    elif ev.get("p1_hit"):     cls.append("ev-p1-white")
    return " ".join(cls) if cls else "ev-idle"


def _bench_html(team: list[dict], active_idx: int) -> str:
    parts = []
    for i, p in enumerate(team):
        if i == active_idx:
            continue
        hp_pct = int(p["current_hp"] / p["hp"] * 100) if p["hp"] else 0
        style  = "text-decoration:line-through;opacity:.4;" if p["fainted"] else ""
        parts.append(
            f'<span style="display:inline-flex;align-items:center;gap:4px;'
            f'background:rgba(255,255,255,.12);border-radius:20px;'
            f'padding:3px 8px;margin:2px;font-size:11px;color:#fff;{style}">'
            f'{p["name"]} <span style="color:#aaa">({hp_pct}%)</span></span>'
        )
    return '<div style="margin-top:6px">' + "".join(parts) + "</div>" if parts else ""


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------
def _init_session():
    if "phase" not in st.session_state:
        st.session_state.phase = "setup"


def _start_battle(p1_names: list[str], poke_map: dict):
    _purge_cheat_db(st.session_state)  # clean any DB changes left by the previous game
    all_pokemon = load_pokemon_list()
    ai_pool     = [p for p in all_pokemon if p["name"] not in p1_names]
    ai_names    = [p["name"] for p in random.sample(ai_pool, min(3, len(ai_pool)))]
    st.session_state.p1_team           = [_make_combatant(poke_map[n]) for n in p1_names]
    st.session_state.p2_team           = [_make_combatant(poke_map[n]) for n in ai_names]
    st.session_state.p1_idx            = 0
    st.session_state.p2_idx            = 0
    st.session_state.turn              = 0
    st.session_state.log               = []
    st.session_state.last_events       = None
    st.session_state.winner            = None
    st.session_state.cheats_used          = []
    st.session_state.cheat_msg            = None
    st.session_state.cheat_nerf_originals = {}
    st.session_state.cheat_audit_findings = None
    st.session_state.phase             = "battle"


def _reset():
    for k in ["phase","p1_team","p2_team","p1_idx","p2_idx",
              "turn","log","last_events","winner","switching",
              "cheats_used","cheat_msg","cheat_nerf_originals","cheat_audit_findings"]:
        st.session_state.pop(k, None)


# ---------------------------------------------------------------------------
# Phase: Setup
# ---------------------------------------------------------------------------
def _render_setup(poke_list: list[dict]):
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        "<h1 style='text-align:center;color:#e74c3c;font-size:2.4rem;"
        "text-shadow:2px 2px 0 #111,4px 4px 0 #7b0000'>⚔️ Pokémon Battle Arena</h1>",
        unsafe_allow_html=True,
    )

    poke_map  = {p["name"]: p for p in poke_list}
    all_names = [p["name"] for p in poke_list]

    st.subheader("Build Your Team — choose 1 to 3 Pokémon")
    selected = st.multiselect(
        "Search & pick your fighters",
        options=all_names,
        max_selections=3,
        placeholder="Type a name to search…",
    )

    # Team preview cards with sprites
    if selected:
        st.subheader("Your Team")
        cols = st.columns(len(selected))
        for col, name in zip(cols, selected):
            p      = poke_map[name]
            badges = _type_badge(p["type1"]) + (_type_badge(p["type2"]) if p["type2"] else "")
            leg    = "★ Legendary" if p["legendary"] else "&nbsp;"
            sprite = SPRITE_BACK.format(p["pokedex_number"])
            fb     = SPRITE_FRONT.format(p["pokedex_number"])
            with col:
                st.markdown(f"""
<div class="poke-card">
  <img src="{sprite}" onerror="this.src='{fb}'">
  <div class="pname">{p['name']}</div>
  <div class="legendary-star" style="font-size:11px;min-height:16px">{leg}</div>
  <div style="margin:4px 0">{badges}</div>
  <div class="pstats">
    HP {p['hp']} &nbsp;·&nbsp; ATK {p['attack']} &nbsp;·&nbsp; DEF {p['defense']}<br>
    SP.ATK {p['sp_atk']} &nbsp;·&nbsp; SP.DEF {p['sp_def']}<br>
    SPEED {p['speed']} &nbsp;·&nbsp; Total {p['total']}
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    start = st.button(
        "⚔️  Start Battle!",
        type="primary",
        use_container_width=True,
        disabled=(len(selected) == 0),
    )
    if start:
        _start_battle(selected, poke_map)
        st.rerun()

    # Battle history
    history = load_battle_history()
    if history:
        st.divider()
        st.subheader("Battle History")
        rows_html = "".join(
            f"<tr><td>{h['timestamp']}</td><td>{h['p1_team']}</td>"
            f"<td>{h['p2_team']}</td><td><b>{h['winner']}</b></td>"
            f"<td style='text-align:center'>{h['turns']}</td></tr>"
            for h in history[:10]
        )
        st.markdown(f"""
<table class="hist-table">
  <tr><th>Time</th><th>Your Team</th><th>AI Team</th><th>Winner</th><th>Rounds</th></tr>
  {rows_html}
</table>""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Phase: Battle
# ---------------------------------------------------------------------------
def _render_battle(chart: dict):
    st.markdown(CSS, unsafe_allow_html=True)
    state   = st.session_state
    p1      = state.p1_team[state.p1_idx]
    p2      = state.p2_team[state.p2_idx]
    ev      = state.get("last_events")
    ev_cls  = _arena_ev_classes(ev)

    p1_hp    = _hp_bar_html(p1, side="p1")
    p2_hp    = _hp_bar_html(p2, side="ai")
    p1_spr   = _sprite_html(p1, is_player=True)
    p2_spr   = _sprite_html(p2, is_player=False)
    p1_bench = _bench_html(state.p1_team, state.p1_idx)
    p2_bench = _bench_html(state.p2_team, state.p2_idx)

    arena_html = f"""
<div class="battle-arena {ev_cls}">

  <!-- AI: HP near AI sprite (right area), bubble tail points right toward sprite -->
  <div style="position:absolute;top:5%;right:24%;">
    {p2_hp}
    {p2_bench}
  </div>

  <!-- AI: sprite + shadow grouped, upper-right area -->
  <div style="position:absolute;top:5%;right:7%;display:flex;flex-direction:column;align-items:center;">
    {p2_spr}
    <div class="shadow-ai"></div>
  </div>

  <!-- Player: sprite + shadow grouped, lower-left area -->
  <div style="position:absolute;bottom:14%;left:7%;display:flex;flex-direction:column;align-items:center;">
    {p1_spr}
    <div class="shadow-p1"></div>
  </div>

  <!-- Player: HP near player sprite (left area), bubble tail points left toward sprite -->
  <div style="position:absolute;bottom:12%;left:26%;">
    {p1_hp}
    {p1_bench}
  </div>

  <!-- Round badge centre -->
  <div style="position:absolute;top:48%;left:50%;transform:translate(-50%,-50%);
              background:rgba(0,0,0,.6);color:#fff;border-radius:20px;
              padding:4px 16px;font-size:13px;font-weight:700;border:1px solid #666;">
    Round {state.turn}
  </div>
</div>"""

    last_msg = state.log[0] if state.log else "What will you do?"
    msg_html = f'<div class="msg-box">{last_msg}</div>'

    st.markdown(arena_html + msg_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    has_bench = any(
        not p["fainted"] for i, p in enumerate(state.p1_team) if i != state.p1_idx
    )

    if st.session_state.get("switching"):
        bench = [(i, p) for i, p in enumerate(state.p1_team)
                 if i != state.p1_idx and not p["fainted"]]
        st.markdown("**Choose a Pokémon to send out:**")
        sw_cols = st.columns(len(bench) + 1)
        for col, (i, p) in zip(sw_cols, bench):
            with col:
                hp_pct = int(p["current_hp"] / p["hp"] * 100) if p["hp"] else 0
                if st.button(f"↪ {p['name']} ({hp_pct}% HP)",
                             use_container_width=True, type="primary"):
                    _do_switch_turn(state, chart, i)
                    st.session_state.switching = False
                    if state.winner:
                        state.phase = "results"
                        _save_battle_log(state)
                    st.rerun()
        with sw_cols[-1]:
            if st.button("✗ Cancel", use_container_width=True):
                st.session_state.switching = False
                st.rerun()
    else:
        col_phys, col_spec, col_sw, col_run = st.columns([2, 2, 1, 1])
        with col_phys:
            if st.button("⚔️  Attack!", type="primary", use_container_width=True):
                _do_round(state, chart, p1_action="physical")
                if state.winner:
                    state.phase = "results"
                    _save_battle_log(state)
                st.rerun()
        with col_spec:
            if st.button("✨  Special!", type="primary", use_container_width=True):
                _do_round(state, chart, p1_action="special")
                if state.winner:
                    state.phase = "results"
                    _save_battle_log(state)
                st.rerun()
        with col_sw:
            if st.button("🔄  Switch", use_container_width=True, disabled=not has_bench):
                st.session_state.switching = True
                st.rerun()
        with col_run:
            if st.button("🏳️  Forfeit", use_container_width=True):
                state.winner = "Player 2 (AI)"
                state.phase  = "results"
                _save_battle_log(state)
                st.rerun()

    # Log history
    if len(state.log) > 1:
        with st.expander(f"📜 Battle Log ({len(state.log)} rounds)"):
            for entry in state.log[1:]:
                st.markdown(f'<div class="log-entry">{entry}</div>',
                            unsafe_allow_html=True)

    # ── Cheat code input ──────────────────────────────────────────────────
    with st.expander("🔑 Enter Cheat Code"):
        st.markdown(
            "<small style='color:#888'>"
            "⬆⬆⬇⬇ <b>UPUPDOWNDOWN</b> — double your team's HP &nbsp;·&nbsp; "
            "🛡️ <b>GODMODE</b> — set active Pokémon DEF &amp; SP.DEF to 999 &nbsp;·&nbsp; "
            "🎯 <b>STEAL</b> — copy AI's strongest Pokémon to your team &nbsp;·&nbsp; "
            "📉 <b>NERF</b> — halve all AI stats &nbsp;·&nbsp; "
            "⭐ <b>LEGENDARY</b> — summon UltraMewtwo"
            "</small>",
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns([3, 1])
        with c1:
            code_input = st.text_input(
                "Cheat code", key="cheat_input_field",
                label_visibility="collapsed",
                placeholder="Type a cheat code and hit Activate…",
            )
        with c2:
            activate = st.button("⚡ Activate", use_container_width=True,
                                 key="cheat_activate_btn")
        if activate:
            code = (code_input or "").strip().upper()
            msg  = _apply_cheat(code, state)
            if msg:
                used = state.get("cheats_used") or []
                used.append(code)
                state["cheats_used"] = used
                state["cheat_msg"]   = msg
            else:
                state["cheat_msg"] = f"❌ Unknown code: {code_input}"
            st.rerun()

    cheat_msg = state.get("cheat_msg")
    if cheat_msg:
        if cheat_msg.startswith("❌"):
            st.error(cheat_msg)
        else:
            st.markdown(f'<div class="cheat-banner">{cheat_msg}</div>',
                        unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Phase: Results
# ---------------------------------------------------------------------------
def _render_results():
    st.markdown(CSS, unsafe_allow_html=True)
    state = st.session_state

    # Run audit and clean DB exactly once (first time results page renders).
    # Findings are cached in session_state so reruns and button clicks don't
    # re-query a now-clean DB.
    if state.get("cheat_audit_findings") is None:
        state["cheat_audit_findings"] = _run_cheat_audit(state.get("cheats_used") or [])
        _purge_cheat_db(state)

    player_won = (state.winner == "Player 1")

    if player_won:
        st.balloons()
        banner = "🏆  You Win!"
    else:
        banner = "💀  The AI Wins!"

    st.markdown(f'<div class="winner-banner">{banner}</div>', unsafe_allow_html=True)
    st.markdown(f"**Battle ended after {state.turn} rounds.**")

    cols = st.columns(2)
    with cols[0]:
        st.subheader("Your Team")
        for p in state.p1_team:
            icon = "✅" if not p["fainted"] else "💀"
            st.markdown(f"{icon} **{p['name']}** — HP {p['current_hp']}/{p['hp']}")
    with cols[1]:
        st.subheader("AI Team")
        for p in state.p2_team:
            icon = "✅" if not p["fainted"] else "💀"
            st.markdown(f"{icon} **{p['name']}** — HP {p['current_hp']}/{p['hp']}")

    with st.expander("📜 Full Battle Log"):
        for entry in state.log:
            st.markdown(f'<div class="log-entry">{entry}</div>',
                        unsafe_allow_html=True)

    history = load_battle_history()
    if history:
        st.divider()
        st.subheader("Battle History")
        rows_html = "".join(
            f"<tr><td>{h['timestamp']}</td><td>{h['p1_team']}</td>"
            f"<td>{h['p2_team']}</td><td><b>{h['winner']}</b></td>"
            f"<td style='text-align:center'>{h['turns']}</td></tr>"
            for h in history[:10]
        )
        st.markdown(f"""
<table class="hist-table">
  <tr><th>Time</th><th>Your Team</th><th>AI Team</th><th>Winner</th><th>Rounds</th></tr>
  {rows_html}
</table>""", unsafe_allow_html=True)

    # ── Cheat audit ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("🔍 Cheat Audit")
    cheats_used = state.get("cheats_used") or []
    if cheats_used:
        tags = " ".join(f'<span class="cheat-tag">{c}</span>' for c in cheats_used)
        st.markdown(f"Cheats activated this battle: {tags}", unsafe_allow_html=True)
    else:
        st.markdown("No cheats used this battle.")
    findings = state.get("cheat_audit_findings") or []
    if findings:
        st.markdown("**DB anomalies / cheat history detected:**")
        for f in findings:
            st.markdown(f"- {f}")
    else:
        st.caption("No anomalous stats found in the DB.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄  Play Again", type="primary", use_container_width=True):
        _reset()
        st.rerun()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(
        page_title="Pokémon Battle Arena",
        page_icon="⚔️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _init_session()
    poke_list = load_pokemon_list()
    chart     = load_type_chart()

    phase = st.session_state.phase
    if   phase == "setup":   _render_setup(poke_list)
    elif phase == "battle":  _render_battle(chart)
    elif phase == "results": _render_results()


if __name__ == "__main__":
    main()
