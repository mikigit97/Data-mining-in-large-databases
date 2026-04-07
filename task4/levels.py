"""
levels.py — Level definitions for the SQL Detective Agency game.

Each level is a dict with:
  num          int          level number (1–6)
  title        str          display title
  concept      str          SQL concept being taught
  story        str          narrative context shown to learner
  task         str          the specific task description
  hint1        str          general concept hint
  hint2        str          specific syntax hint
  story_update str          text shown after level is solved
  check_fn     callable     (df) -> bool — True if answer is correct
  diagnose_fn  callable     (df, query) -> str — specific wrong-answer message
"""
import pandas as pd

_SUSPECT_COLS = {"suspect_id", "name", "age", "occupation", "district", "motive_score", "known_associate"}


def _check_1(df: pd.DataFrame) -> bool:
    return len(df) == 25 and set(df.columns) == _SUSPECT_COLS


def _diagnose_1(df: pd.DataFrame, query: str) -> str:
    if df is None or len(df) == 0:
        return "No rows returned. Make sure you're querying the `suspects` table."
    if len(df) != 25:
        return f"Expected 25 rows but got {len(df)}. Are you querying the right table?"
    missing = _SUSPECT_COLS - set(df.columns)
    if missing:
        return f"Missing columns: {missing}. Use SELECT * to get all columns."
    return "Close — double-check your table name and column selection."


def _check_2(df: pd.DataFrame) -> bool:
    if len(df) != 5:
        return False
    if "district" not in df.columns:
        return False
    return (df["district"] == "Docklands").all()


def _diagnose_2(df: pd.DataFrame, query: str) -> str:
    if df is None or len(df) == 0:
        return "No rows returned. Check the spelling of 'Docklands' — it's case-sensitive."
    if len(df) == 25:
        return "All 25 suspects returned — you need a WHERE clause to filter by district."
    if "district" not in df.columns:
        return "The `district` column is missing. Use SELECT * to include all columns."
    if not (df["district"] == "Docklands").all():
        return "Some rows don't have district = 'Docklands'. Check your WHERE condition."
    if len(df) != 5:
        return f"Expected 5 Docklands suspects but got {len(df)}. Check your filter value."
    return "Almost — re-read the WHERE clause condition."


def _check_3(df: pd.DataFrame) -> bool:
    if len(df) != 3:
        return False
    if "motive_score" not in df.columns:
        return False
    return list(df["motive_score"]) == [9, 9, 8]


def _diagnose_3(df: pd.DataFrame, query: str) -> str:
    if df is None or len(df) == 0:
        return "No rows returned. Make sure you're querying the `suspects` table."
    if len(df) > 3:
        return f"Got {len(df)} rows — you need a LIMIT clause to return only the top 3."
    if "motive_score" not in df.columns:
        return "The `motive_score` column is missing. Use SELECT * or include it explicitly."
    if len(df) == 3 and list(df["motive_score"]) != [9, 9, 8]:
        return "You have 3 rows but they're not in the right order. Add ORDER BY motive_score DESC."
    return "Check your ORDER BY direction — you want the highest score first (DESC)."


def _check_4(df: pd.DataFrame) -> bool:
    if set(df.columns) != {"district", "crime_count"}:
        return False
    if len(df) != 5:
        return False
    first = df.iloc[0].to_dict()
    return first.get("district") == "Docklands" and int(first.get("crime_count", 0)) == 10


def _diagnose_4(df: pd.DataFrame, query: str) -> str:
    if df is None or len(df) == 0:
        return "No rows returned. Make sure you're querying the `crimes` table with GROUP BY district."
    if "crime_count" not in df.columns:
        cols = list(df.columns)
        return f"Expected a column named `crime_count` but got: {cols}. Use COUNT(*) AS crime_count."
    if len(df) != 5:
        return f"Expected 5 rows (one per district) but got {len(df)}. Check your GROUP BY clause."
    if df.iloc[0].get("district") != "Docklands":
        return "Results aren't sorted correctly. Add ORDER BY crime_count DESC so Docklands appears first."
    if int(df.iloc[0].get("crime_count", 0)) != 10:
        return "The count for Docklands should be 10. Check you're counting from the `crimes` table."
    return "Close — double-check your GROUP BY and ORDER BY clauses."


def _check_5(df: pd.DataFrame) -> bool:
    if set(df.columns) != {"name", "district", "evidence_type"}:
        return False
    if len(df) != 4:
        return False
    return (df["evidence_type"] == "Physical").all()


def _diagnose_5(df: pd.DataFrame, query: str) -> str:
    if df is None or len(df) == 0:
        return "No rows returned. Make sure you JOIN suspects and evidence on suspect_id."
    expected_cols = {"name", "district", "evidence_type"}
    if set(df.columns) != expected_cols:
        missing = expected_cols - set(df.columns)
        extra = set(df.columns) - expected_cols
        msg = ""
        if missing:
            msg += f"Missing columns: {missing}. "
        if extra:
            msg += f"Remove extra columns: {extra}. "
        return msg + "Select exactly: name, district, evidence_type."
    if len(df) != 4:
        if not (df["evidence_type"] == "Physical").all():
            return "Some rows have evidence_type != 'Physical'. Add WHERE evidence_type = 'Physical'."
        return f"Expected 4 Physical evidence rows but got {len(df)}. Check your JOIN and WHERE clause."
    if not (df["evidence_type"] == "Physical").all():
        return "Your JOIN worked but the WHERE filter isn't right. Filter to evidence_type = 'Physical'."
    return "Almost there — check your SELECT columns and JOIN condition."


def _check_6(df: pd.DataFrame) -> bool:
    if set(df.columns) != {"suspect_id", "evidence_count"}:
        return False
    counts = sorted(df["evidence_count"].tolist(), reverse=True)
    return counts[0] >= 2 and len(df) >= 2


def _diagnose_6(df: pd.DataFrame, query: str) -> str:
    if df is None or len(df) == 0:
        return "No rows returned. Use GROUP BY suspect_id on the `evidence` table."
    if "evidence_count" not in df.columns:
        return "Name the count column `evidence_count` using COUNT(*) AS evidence_count."
    if len(df) == 0:
        return "No results — check your HAVING clause threshold."
    if df["evidence_count"].max() < 2:
        return "All counts are 1 — make sure HAVING COUNT(*) > 1 filters correctly."
    return "Close — check you're ordering by evidence_count DESC."


LEVELS = [
    {
        "num": 1,
        "title": "Open the Case Files",
        "concept": "SELECT *",
        "story": (
            "Detective, you've just been assigned to the most complex case this city has seen. "
            "Before anything else, you need to know who we're dealing with. "
            "Pull the complete suspect database — every name, every background, every detail."
        ),
        "task": (
            "Write a query to retrieve ALL columns and ALL rows from the `suspects` table."
        ),
        "hint1": (
            "The `SELECT` statement retrieves data from a table. "
            "The `*` wildcard means 'all columns'. "
            "The `FROM` keyword tells SQL which table to look in."
        ),
        "hint2": "Try: SELECT * FROM suspects",
        "story_update": (
            "25 names now spread across your desk. One of them is guilty. "
            "Study the records — the truth is in the details."
        ),
        "correct_query_lines": [
            "SELECT *",
            "FROM suspects",
        ],
        "check_fn": _check_1,
        "diagnose_fn": _diagnose_1,
    },
    {
        "num": 2,
        "title": "Narrow the Suspects",
        "concept": "WHERE",
        "story": (
            "A reliable informant places the perpetrator in the **Docklands** district. "
            "That's our hunting ground. We can't investigate 25 people — "
            "narrow the list to only those who operate in Docklands."
        ),
        "task": (
            "Retrieve all columns from `suspects` where the `district` is `'Docklands'`."
        ),
        "hint1": (
            "The `WHERE` clause filters rows. Only rows where the condition is true are included. "
            "Place it after the table name: SELECT ... FROM table WHERE condition"
        ),
        "hint2": (
            "Text values in SQL need single quotes. "
            "Try: SELECT * FROM suspects WHERE district = 'Docklands'"
        ),
        "story_update": (
            "Five suspects operate in Docklands. The investigation narrows considerably. "
            "Alex Crane and Jordan Voss are already on our radar — both based in Docklands."
        ),
        "correct_query_lines": [
            "SELECT * FROM suspects",
            "WHERE district = 'Docklands'",
        ],
        "check_fn": _check_2,
        "diagnose_fn": _diagnose_2,
    },
    {
        "num": 3,
        "title": "Top Suspects",
        "concept": "ORDER BY / LIMIT",
        "story": (
            "The chief is breathing down your neck — she wants a shortlist, not a case file. "
            "Every suspect has a `motive_score` from 1 to 10. "
            "Rank them and hand over just the top 3."
        ),
        "task": (
            "Query `suspects`, order by `motive_score` from highest to lowest, "
            "and return only the top 3 rows. Include all columns."
        ),
        "hint1": (
            "ORDER BY column sorts results. To sort largest-first, add DESC. "
            "LIMIT n restricts how many rows are returned. "
            "Both go at the end of your query."
        ),
        "hint2": "End your query with: ORDER BY motive_score DESC LIMIT 3",
        "story_update": (
            "Alex Crane scores a 9. So does Jordan Voss. Taylor Ashford sits just behind at 8. "
            "Eyes on these three."
        ),
        "correct_query_lines": [
            "SELECT *",
            "FROM suspects",
            "ORDER BY motive_score DESC",
            "LIMIT 3",
        ],
        "check_fn": _check_3,
        "diagnose_fn": _diagnose_3,
    },
    {
        "num": 4,
        "title": "Crime by District",
        "concept": "GROUP BY / COUNT",
        "story": (
            "Command wants a situation report. Which districts are the hotspots? "
            "You need to count how many crimes have been filed in each district "
            "and rank them from most active to least."
        ),
        "task": (
            "From the `crimes` table, count the number of crimes per `district`. "
            "Name the count column `crime_count`. "
            "Order results from most to fewest crimes."
        ),
        "hint1": (
            "GROUP BY collapses all rows that share the same value into one row. "
            "COUNT(*) counts how many rows were in each group. "
            "Use AS to name the result column."
        ),
        "hint2": (
            "Full structure: "
            "SELECT district, COUNT(*) AS crime_count "
            "FROM crimes GROUP BY district ORDER BY crime_count DESC"
        ),
        "story_update": (
            "Docklands tops the chart with 10 reported crimes — more than any other district. "
            "This is not a coincidence. Our suspects and our crime hotspot overlap perfectly."
        ),
        "correct_query_lines": [
            "SELECT district, COUNT(*) AS crime_count",
            "FROM crimes",
            "GROUP BY district",
            "ORDER BY crime_count DESC",
        ],
        "check_fn": _check_4,
        "diagnose_fn": _diagnose_4,
    },
    {
        "num": 5,
        "title": "Connect the Evidence",
        "concept": "JOIN",
        "story": (
            "The forensics team just delivered the evidence log. "
            "It links suspects directly to crime scenes. "
            "Your job: cross-reference it with the suspect records. "
            "Find every suspect who has **Physical** evidence against them."
        ),
        "task": (
            "Join `suspects` and `evidence` on `suspect_id`. "
            "Filter to rows where `evidence_type = 'Physical'`. "
            "Return only the suspect's `name`, `district`, and `evidence_type`."
        ),
        "hint1": (
            "JOIN links two tables using a shared column. "
            "INNER JOIN only returns rows where the key exists in both tables. "
            "Syntax: FROM table1 JOIN table2 ON table1.col = table2.col"
        ),
        "hint2": (
            "Try: "
            "SELECT suspects.name, suspects.district, evidence.evidence_type "
            "FROM suspects JOIN evidence ON suspects.suspect_id = evidence.suspect_id "
            "WHERE evidence.evidence_type = 'Physical'"
        ),
        "story_update": (
            "Four suspects have physical evidence against them. "
            "Alex Crane, Jordan Voss, Taylor Ashford, and Stav Wolfe. "
            "Cross-reference with motive scores — the case is almost cracked."
        ),
        "correct_query_lines": [
            "SELECT suspects.name, suspects.district, evidence.evidence_type",
            "FROM suspects",
            "JOIN evidence ON suspects.suspect_id = evidence.suspect_id",
            "WHERE evidence.evidence_type = 'Physical'",
        ],
        "check_fn": _check_5,
        "diagnose_fn": _diagnose_5,
    },
    {
        "num": 6,
        "title": "The Mastermind",
        "concept": "GROUP BY + HAVING",
        "story": (
            "One final case, Detective — and it's the hardest yet. "
            "Someone is connected to **multiple crimes** through the evidence log. "
            "That's our mastermind. Find every suspect_id that appears more than once "
            "in the evidence table. These are the repeat offenders."
        ),
        "task": (
            "Using the `evidence` table, find all `suspect_id` values that appear "
            "in more than one row. "
            "Show `suspect_id` and their count as `evidence_count`, "
            "ordered by count descending."
        ),
        "hint1": (
            "HAVING is like WHERE but it filters groups after GROUP BY. "
            "You can use aggregate functions like COUNT(*) inside a HAVING condition."
        ),
        "hint2": (
            "Structure: "
            "SELECT suspect_id, COUNT(*) AS evidence_count "
            "FROM evidence GROUP BY suspect_id HAVING COUNT(*) > 1 "
            "ORDER BY evidence_count DESC"
        ),
        "story_update": (
            "Three suspects appear repeatedly in the evidence. "
            "Alex Crane leads with the most links. The Agency is preparing the arrest warrant. "
            "Outstanding work, Detective."
        ),
        "correct_query_lines": [
            "SELECT suspect_id, COUNT(*) AS evidence_count",
            "FROM evidence",
            "GROUP BY suspect_id",
            "HAVING COUNT(*) > 1",
            "ORDER BY evidence_count DESC",
        ],
        "check_fn": _check_6,
        "diagnose_fn": _diagnose_6,
    },
]

LEVEL_MAP = {lvl["num"]: lvl for lvl in LEVELS}

STORY_UPDATES = {lvl["num"]: lvl["story_update"] for lvl in LEVELS}

ALL_COMPLETE_TEXT = (
    "You have enough to make an arrest. "
    "Alex Crane and their Docklands network are in custody. "
    "The Detective Agency commends your service, Chief Inspector. "
    "The city sleeps a little safer tonight."
)
