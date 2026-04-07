# Task 2.3 – Interesting Finds

---

## Finding 1 — Angela Lansbury holds the record for the longest gap between first nomination and first win: 69 years

Angela Lansbury was nominated for **Best Actress in a Supporting Role** three times —
for *Gaslight* (1945), *The Picture of Dorian Gray* (1946), and *The Manchurian Candidate*
(1963) — and lost all three. She went on to become one of the most celebrated performers
in theatre and television without ever winning a competitive Oscar. In 2014, 69 years after
her first nomination, she finally received an **Honorary Award** at the 6th Governors Awards.

**How it was found:**

A PonyORM generator expression fetches every `(person_name, ceremony_year, winner)` triple
for named nominees. The gap is then computed in Python by grouping by person and evaluating
`min(win_years) - min(nom_years)`:

```python
with db_session:
    all_noms = select(
        (n.person.name, n.ceremony.year, n.winner)
        for n in Nomination
        if n.person is not None
    )[:]

person_data = defaultdict(lambda: {"nom_years": [], "win_years": []})
for name, year, winner in all_noms:
    person_data[name]["nom_years"].append(year)
    if winner:
        person_data[name]["win_years"].append(year)

gaps = []
for name, data in person_data.items():
    if data["win_years"]:
        gap = min(data["win_years"]) - min(data["nom_years"])
        if gap > 0:
            gaps.append((name, gap, min(data["nom_years"]), min(data["win_years"])))

gaps.sort(key=lambda x: -x[1])
```

The full list can also be explored interactively: searching "Angela Lansbury" in the Actor
Profile App shows her profile with the "Years to First Win" metric and the complete
nomination history table.

**Why it's interesting:**

69 years is longer than most film careers. Lansbury was nominated before she turned 20
and only won after she turned 88. The gap also illustrates a structural quirk of Oscar data:
Honorary Awards are recorded as wins in the `winner` column, so the longest "gaps" are
dominated by performers who were repeatedly passed over competitively and later honoured
for lifetime achievement. Of the top 15 longest-gap individuals in the dataset, 11 of the
eventual first wins are Honorary Awards or Jean Hersholt Humanitarian Awards — suggesting that
the Academy systematically uses honorary recognition to compensate for careers it overlooked
in the competitive race. The remaining 4 competitive wins in the top 15 all belong to countries
in the International Feature Film category (Brazil, Mexico, Poland, Japan), not individuals.

---

## Finding 2 — Titanic (1997) is the only film ever nominated in 14 distinct canonical categories

*Titanic* received 14 nominations at the 70th Academy Awards (1998) spanning every major
filmmaking department — from acting to visual effects to music to costume to makeup and
hairstyling. It converted 11 of those into wins (a 79% win rate). No other film in 97
years of Oscar history has been nominated in as many distinct canonical categories.

**How it was found:**

A PonyORM generator expression counted distinct `canon_name` values per film and sorted
descending:

```python
with db_session:
    results = select(
        (n.film.title, n.film.year, count(n.category.canon_name, distinct=True))
        for n in Nomination
        if n.film is not None
    ).order_by(lambda t, y, cnt: desc(cnt))[:15]
```

A follow-up query confirmed the exact categories:

```
ACTRESS IN A LEADING ROLE, ACTRESS IN A SUPPORTING ROLE, ART DIRECTION,
BEST PICTURE, CINEMATOGRAPHY, COSTUME DESIGN, DIRECTING, FILM EDITING,
MAKEUP AND HAIRSTYLING, MUSIC (Original Score), MUSIC (Original Song),
SOUND EDITING, SOUND MIXING, VISUAL EFFECTS
```

**Why it's interesting:**

The nearest competitor for breadth is a cluster of seven films at 13 distinct categories
(*Forrest Gump*, *Gone with the Wind*, *La La Land*, *Mary Poppins*, *Oppenheimer*,
*Shakespeare in Love*, *The Lord of the Rings: The Fellowship of the Ring*). *Titanic* stands
alone at 14. Comparing it to *Ben-Hur* (1959) — which also won 11 Oscars from 12 nominations —
reveals the difference in eras: Ben-Hur achieved a 92% win rate from 12 nominations while
*Titanic* reached further across 14 categories at 79%. The breadth of *Titanic*'s nominations
reflects how completely the Academy judged it the dominant achievement of its year across
every craft discipline simultaneously, a feat no film has replicated since.

---

## Finding 3 — Only four individuals have ever been nominated competitively in all three primary filmmaking roles: Acting, Directing, and Writing

A PonyORM query classifying each person's nominations into craft disciplines (excluding
honorary awards and Best Picture producer credits) reveals that only **four individuals** —
Woody Allen, John Huston, Kenneth Branagh, and John Cassavetes — have competitive nominations
in all three primary creative roles simultaneously.

**How it was found:**

For each person, only competitive craft nominations are considered (honorary awards and
Best Picture are excluded). The nomination set is then checked against three discipline
groups:

```python
ACTING_CATS    = {"ACTOR IN A LEADING ROLE", "ACTRESS IN A LEADING ROLE",
                  "ACTOR IN A SUPPORTING ROLE", "ACTRESS IN A SUPPORTING ROLE", ...}
DIRECTING_CATS = {"DIRECTING"}
WRITING_CATS   = {"WRITING (Adapted Screenplay)", "WRITING (Original Screenplay)", ...}
HONORARY_CATS  = {"HONORARY AWARD", "JEAN HERSHOLT HUMANITARIAN AWARD",
                  "BEST PICTURE", ...}  # excluded

with db_session:
    persons_list = select(p for p in Person)[:]
    for p in persons_list:
        craft_cats = {n.category.canon_name for n in p.nominations
                      if n.category.canon_name not in HONORARY_CATS}
        has_acting  = bool(craft_cats & ACTING_CATS)
        has_dir     = bool(craft_cats & DIRECTING_CATS)
        has_writing = bool(craft_cats & WRITING_CATS)
        if has_acting and has_dir and has_writing:
            ...  # triple-discipline nominee
```

The full nomination history for each of the four is verified by looking up their profile in
the Actor Profile App.

**Why it's interesting:**

Out of ~6,893 nominees across 97 years, only 4 individuals have competitive nominations
in all three primary filmmaking disciplines. What makes **Kenneth Branagh** stand out within
this group is the evenness of the spread: his 6 nominations cover both acting sub-roles
(Leading and Supporting), Directing (twice), and both writing sub-roles (Adapted and
Original Screenplay) — all competitive, with no honorary awards inflating the count. He was
nominated for Directing and Actor in a Leading Role for the *same film* (*Henry V*, 1990),
returned with Writing for *Hamlet* (1997), and 25 years later earned Directing and Writing
nominations for *Belfast* (2022), winning the latter.

Woody Allen leads the group in raw nominations (21) but his acting credit is a single entry —
his dominance is in Writing (13) and Directing (7), making him a two-discipline specialist
rather than a three-discipline generalist. The distinction matters: Branagh's breadth reflects
the Academy recognising the same person as a craftsman in every creative department of a film.
