"""
Task 2.2 – Oscar Actor Profile App
Streamlit app combining Oscar nomination data (PonyORM) with Wikipedia bios.
Run with:  task2/.venv311/Scripts/streamlit run task2/app2.py
"""
import os
import random
import requests
import streamlit as st
import pandas as pd
from pony.orm import (
    Database, PrimaryKey, Required, Optional, Set, composite_key,
    db_session, select, count, desc,
)

st.set_page_config(
    page_title="Oscar Explorer",
    page_icon=":trophy:",
    layout="wide",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "oscar.db")


# ── All ORM setup inside @st.cache_resource so it runs exactly once ───────────
# Streamlit reruns the module on every interaction; putting entity definitions
# at module level means a new unbound Database() is created each time while
# @st.cache_resource skips re-binding — causing ERDiagramError.
# Solution: define everything inside the cached function and re-assign
# module-level names from the cached return value on each rerun.

@st.cache_resource
def _setup_db():
    _db = Database()

    class Ceremony(_db.Entity):
        number      = PrimaryKey(int)
        year        = Required(int)
        nominations = Set("Nomination")

    class Category(_db.Entity):
        name        = Required(str, unique=True)
        canon_name  = Required(str)
        nominations = Set("Nomination")

    class Person(_db.Entity):
        name        = Required(str, unique=True)
        nominations = Set("Nomination")

    class Film(_db.Entity):
        title       = Required(str)
        year        = Required(int)
        nominations = Set("Nomination")
        composite_key(title, year)

    class Nomination(_db.Entity):
        ceremony = Required(Ceremony)
        category = Required(Category)
        person   = Optional(Person)
        film     = Optional(Film)
        winner   = Required(bool)

    _db.bind(provider="sqlite", filename=DB_PATH, create_db=False)
    _db.generate_mapping()
    return _db, Ceremony, Category, Person, Film, Nomination


db, Ceremony, Category, Person, Film, Nomination = _setup_db()


# ── DB queries ────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def search_persons(query: str) -> list:
    """Return sorted list of person names containing the query string."""
    q = query.strip().lower()
    if not q:
        return []
    with db_session:
        return sorted(
            select(p.name for p in Person if q in p.name.lower())[:]
        )


@st.cache_data(show_spinner=False)
def get_profile(name: str) -> dict | None:
    return _load_profile(name)


@db_session
def _load_profile(name: str) -> dict | None:
    person = Person.get(name=name)
    if not person:
        return None

    noms = select(n for n in Nomination if n.person == person)[:]

    total_noms = len(noms)
    total_wins = sum(1 for n in noms if n.winner)
    win_rate   = total_wins / total_noms if total_noms else 0.0

    categories     = sorted({n.category.canon_name for n in noms})
    years          = sorted({n.ceremony.year for n in noms})
    first_nom_year = years[0] if years else None
    win_years      = sorted(n.ceremony.year for n in noms if n.winner)
    first_win_year = win_years[0] if win_years else None
    years_to_win   = (
        first_win_year - first_nom_year
        if first_win_year is not None and first_nom_year is not None
        else None
    )

    films_data = sorted(
        [
            {
                "Film":     n.film.title if n.film else "—",
                "Year":     n.ceremony.year,
                "Category": n.category.canon_name,
                "Win":      "Yes" if n.winner else "",
            }
            for n in noms
        ],
        key=lambda x: (x["Year"], x["Film"]),
    )

    # Per-category comparison: how this person's count compares to the average
    cat_comparisons = []
    for cat_name in categories:
        cat_counts = select(
            (n.person.name, count(n))
            for n in Nomination
            if n.category.canon_name == cat_name and n.person is not None
        )[:]
        if cat_counts:
            avg = sum(c for _, c in cat_counts) / len(cat_counts)
            person_count = sum(1 for n in noms if n.category.canon_name == cat_name)
            cat_comparisons.append({
                "Category":     cat_name,
                "Your Noms":    person_count,
                "Category Avg": f"{avg:.2f}",
                "Ratio":        f"{person_count / avg:.1f}x" if avg else "—",
            })

    # Nomination percentile across all nominees (for Did You Know)
    all_counts = select(
        (p2.name, count(n2))
        for p2 in Person
        for n2 in p2.nominations
    )[:]
    nom_counts = [c for _, c in all_counts]
    nom_pct = (
        sum(1 for c in nom_counts if c < total_noms) / len(nom_counts) * 100
        if nom_counts else 0
    )

    did_you_know = _pick_fact(
        name, total_noms, total_wins, years, categories,
        first_nom_year, first_win_year, years_to_win, nom_pct,
    )

    return {
        "name":            name,
        "total_noms":      total_noms,
        "total_wins":      total_wins,
        "win_rate":        win_rate,
        "categories":      categories,
        "years":           years,
        "first_nom_year":  first_nom_year,
        "first_win_year":  first_win_year,
        "years_to_win":    years_to_win,
        "films":           films_data,
        "cat_comparisons": cat_comparisons,
        "did_you_know":    did_you_know,
    }


def _pick_fact(
    name, total_noms, total_wins, years, categories,
    first_nom_year, first_win_year, years_to_win, nom_pct,
) -> str:
    facts = []

    if nom_pct >= 75:
        facts.append(
            f"{name} has more Oscar nominations than {nom_pct:.0f}% "
            f"of all nominees in Academy history."
        )
    if total_wins >= 3:
        facts.append(f"{name} is a {total_wins}-time Oscar winner.")
    if total_wins > 0 and years_to_win == 0:
        facts.append(
            f"{name} won an Oscar at the very first ceremony they were nominated ({first_win_year})."
        )
    if years_to_win is not None and years_to_win >= 10:
        facts.append(
            f"{name} waited {years_to_win} years for their first Oscar win "
            f"({first_nom_year} → {first_win_year})."
        )
    if total_wins == 0 and total_noms >= 4:
        facts.append(
            f"Despite {total_noms} Oscar nominations, {name} has never won the award."
        )
    if len(years) > 1 and (years[-1] - years[0]) >= 20:
        facts.append(
            f"{name}'s Oscar career spans {years[-1] - years[0]} years "
            f"({years[0]}–{years[-1]})."
        )
    if len(categories) >= 3:
        facts.append(
            f"{name} has been nominated in {len(categories)} different Oscar categories."
        )

    if not facts:
        facts.append(
            f"{name} has {total_noms} Oscar nomination{'s' if total_noms != 1 else ''} "
            f"across {len(categories)} {'category' if len(categories) == 1 else 'categories'}."
        )

    # Deterministic per person so the card is stable across reruns
    random.seed(name)
    result = random.choice(facts)
    random.seed()
    return result


# ── Wikipedia (REST API) ──────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_wiki(name: str) -> dict | None:
    """
    Fetch summary + thumbnail from the Wikipedia REST summary endpoint.
    Falls back to common disambiguation suffixes if the plain name returns
    a disambiguation page or 404.
    """
    headers = {"User-Agent": "OscarExplorer/1.0 (homework project)"}

    def _try(title: str) -> dict | None:
        url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + title.replace(" ", "_")
        )
        try:
            r = requests.get(url, timeout=6, headers=headers)
            if r.status_code != 200:
                return None
            d = r.json()
            if d.get("type") in ("disambiguation", "no-extract"):
                return None
            return {
                "summary":    d.get("extract", ""),
                "photo_url":  (d.get("thumbnail") or {}).get("source"),
                "page_url":   (
                    d.get("content_urls", {})
                     .get("desktop", {})
                     .get("page", "")
                ),
                "page_title": d.get("titles", {}).get("canonical", ""),
            }
        except Exception:
            return None

    def _birth_date(page_title: str) -> str | None:
        try:
            # Step 1: get Wikidata entity ID via Wikipedia API
            r1 = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query", "prop": "pageprops",
                    "ppprop": "wikibase_item", "titles": page_title,
                    "format": "json",
                },
                timeout=5, headers=headers,
            )
            pages = r1.json().get("query", {}).get("pages", {})
            qid = next(iter(pages.values()), {}).get("pageprops", {}).get("wikibase_item")
            if not qid:
                return None
            # Step 2: get P569 (date of birth) from Wikidata
            r2 = requests.get(
                "https://www.wikidata.org/w/api.php",
                params={
                    "action": "wbgetentities", "ids": qid,
                    "props": "claims", "format": "json",
                },
                timeout=5, headers=headers,
            )
            claims = r2.json().get("entities", {}).get(qid, {}).get("claims", {})
            p569 = claims.get("P569", [])
            if not p569:
                return None
            time_val = p569[0]["mainsnak"]["datavalue"]["value"]["time"]
            # Format: "+1949-06-22T00:00:00Z"
            from datetime import date as _date
            d = _date.fromisoformat(time_val.lstrip("+").split("T")[0])
            return d.strftime("%B %d, %Y")
        except Exception:
            return None

    result = _try(name)
    if result:
        result["birth_date"] = _birth_date(result["page_title"])
        return result
    for suffix in ["(actor)", "(actress)", "(film director)", "(composer)"]:
        result = _try(f"{name} {suffix}")
        if result:
            result["birth_date"] = _birth_date(result["page_title"])
            return result
    return None


# ── UI ────────────────────────────────────────────────────────────────────────

def render_profile(profile: dict, wiki: dict | None) -> None:
    name = profile["name"]

    # Header row: photo + name
    col_photo, col_title = st.columns([1, 5])
    with col_photo:
        if wiki and wiki.get("photo_url"):
            st.image(wiki["photo_url"], width=150)
    with col_title:
        st.title(name)
        if wiki and wiki.get("birth_date"):
            st.markdown(f"**Born:** {wiki['birth_date']}")
        if wiki and wiki.get("page_url"):
            st.caption(f"[Wikipedia biography]({wiki['page_url']})")

    st.divider()

    # Key metrics row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Nominations",       profile["total_noms"])
    c2.metric("Wins",              profile["total_wins"])
    c3.metric("Win Rate",          f"{profile['win_rate']:.0%}")
    c4.metric("First Nominated",   profile["first_nom_year"] or "—")
    c5.metric("Last Nominated",    profile["years"][-1] if profile["years"] else "—")
    ytw_display = (
        "Same year" if profile["years_to_win"] == 0
        else str(profile["years_to_win"]) if profile["years_to_win"] is not None
        else "—"
    )
    c6.metric("Years to First Win", ytw_display)

    # First-win callout
    ytw = profile["years_to_win"]
    if ytw == 0:
        st.success(
            f"Won at their first nominated ceremony ({profile['first_win_year']})."
        )
    elif ytw is not None:
        st.info(
            f"Waited **{ytw} year(s)** from first nomination "
            f"({profile['first_nom_year']}) to first win ({profile['first_win_year']})."
        )
    elif profile["total_noms"] > 0 and profile["total_wins"] == 0:
        st.warning(
            f"{name} has {profile['total_noms']} nomination"
            f"{'s' if profile['total_noms'] != 1 else ''} but has never won."
        )

    st.divider()

    left, right = st.columns(2)

    with left:
        # Biography
        st.subheader("Biography")
        if wiki and wiki.get("summary"):
            st.write(wiki["summary"])
        else:
            st.caption("Wikipedia page not found for this person.")

        # Nominated categories
        st.subheader("Categories")
        for cat in profile["categories"]:
            st.markdown(f"- {cat}")

    with right:
        # Category comparison table
        st.subheader("vs. Category Average")
        st.caption(
            "How many times this person was nominated in each category "
            "vs. the average across all nominees in that category."
        )
        if profile["cat_comparisons"]:
            st.dataframe(
                pd.DataFrame(profile["cat_comparisons"]),
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption("No comparison data available.")

        # Did You Know bonus feature
        if profile.get("did_you_know"):
            st.subheader("Did You Know?")
            st.info(profile["did_you_know"])

    st.divider()

    # Full nomination history table
    st.subheader("Nomination History")
    if profile["films"]:
        st.dataframe(
            pd.DataFrame(profile["films"]),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.caption("No nomination records found.")


QUICK_PICKS = [
    "Meryl Streep",
    "Jack Nicholson",
    "Katharine Hepburn",
    "Steven Spielberg",
    "Martin Scorsese",
    "Cate Blanchett",
    "Daniel Day-Lewis",
    "Audrey Hepburn",
    "Woody Allen",
    "Clint Eastwood",
]

_PLACEHOLDER = "— choose a name —"


def main():
    st.sidebar.title("Oscar Explorer")
    st.sidebar.write(
        "Search for any Academy Award nominee — actor, director, composer, or studio."
    )

    mode = st.sidebar.radio(
        "How would you like to find a nominee?",
        ["Pick from list", "Search by name"],
        horizontal=True,
    )

    selected = None

    if mode == "Pick from list":
        quick_pick = st.sidebar.selectbox(
            "Notable nominees",
            [_PLACEHOLDER] + QUICK_PICKS,
        )
        if quick_pick == _PLACEHOLDER:
            st.markdown("## Oscar Explorer")
            st.write(
                "Select a name from the dropdown to see nomination history, "
                "Wikipedia biography, win statistics, and a comparison to category peers."
            )
            return
        selected = quick_pick

    else:  # Search by name
        query = st.sidebar.text_input("Name", placeholder="e.g. Meryl Streep")
        if not query.strip():
            st.markdown("## Oscar Explorer")
            st.write(
                "Type a name in the search box to see nomination history, "
                "Wikipedia biography, win statistics, and a comparison to category peers."
            )
            return

        with st.spinner("Searching…"):
            matches = search_persons(query)

        if not matches:
            st.sidebar.error("No nominees found. Try a different spelling.")
            st.info(
                f"No Oscar nominees matched **{query}**. "
                "Names are matched as substrings, so partial names work too."
            )
            return

        if len(matches) == 1:
            selected = matches[0]
        else:
            st.sidebar.caption(f"{len(matches)} matches found:")
            selected = st.sidebar.radio("Select a person:", matches, label_visibility="collapsed")

    if not selected:
        return

    with st.spinner(f"Loading profile for {selected}…"):
        profile = get_profile(selected)
        wiki    = fetch_wiki(selected)

    if not profile:
        st.error(f"Could not load profile for '{selected}'.")
        return

    render_profile(profile, wiki)


main()
