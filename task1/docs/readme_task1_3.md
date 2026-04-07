# Task 1.3 – Pattern Discovery

## What I Built and How It Works

I used the existing Baby Names Explorer app (Tab B — Custom SQL Query Panel) together with
direct SQLite queries to interrogate the `national_names` table and surface three non-obvious
patterns. Each pattern was discovered by running aggregation queries, then verified visually
in the app.

---

## Technologies & Libraries

| Technology | Why chosen |
|---|---|
| **SQLite / sqlite3** | All queries run directly against the existing `baby_names.db` — no extra tooling needed. Window functions (`ROW_NUMBER OVER PARTITION`) made decade-level ranking possible in a single query. |
| **pandas** | Used for post-query calculations (e.g. percentage share, ratio columns) and to verify the numbers before writing the findings up. |
| **Streamlit app / Plotly** | Tab A (line chart) and Tab B (bar chart) were used to visually confirm and present each pattern interactively. |

---

## Pattern 1 — The Baby Boom Created the Biggest Single-Name Spike in History

**Finding:** Linda gained **+47,072 births in a single year** (1946 → 1947: from 52,823 to
99,895), the largest absolute one-year jump of any name in the entire 134-year dataset. It
simultaneously displaced Mary from the #1 position — ending a reign that had lasted since
records began in 1880.

**Query that reveals it:**
```sql
SELECT a.Name, a.Year,
       a.Count AS ThisYear,
       b.Count AS PrevYear,
       (a.Count - b.Count) AS Jump
FROM (SELECT Name, Year, SUM(Count) AS Count
      FROM national_names GROUP BY Name, Year) a
JOIN (SELECT Name, Year, SUM(Count) AS Count
      FROM national_names GROUP BY Name, Year) b
  ON a.Name = b.Name AND a.Year = b.Year + 1
WHERE b.Count > 1000
ORDER BY Jump DESC
LIMIT 15
```

*To visualise: enter "Linda" in Tab A — the 1947 peak is unmistakable.*

**Interpretation:** Linda's 1930s rise was triggered by two Hollywood hits — *Accent on
Youth* (1935) and *Wife vs. Secretary* (1936) — both featuring prominent characters named
Linda, whose release years map directly onto the data's acceleration. The specific 1947
explosion has a second cause: Jack Lawrence's song *"Linda"*, written for baby Linda
Eastman (future wife of Paul McCartney) and recorded by Buddy Clark, hit **#1 on the US
charts in early 1947** — exactly as the post-war baby boom drove a 33.9% surge in total
births. The spike is a three-way compounding: two priming films + a #1 pop song + a
demographic surge. Linda then declined nearly as steeply — once a name belongs to one
generation, the next actively avoids it.
[[source 1]](https://myhistoryfix.com/entertainment/linda-name-generation/)
[[source 2]](https://www.mentalfloss.com/article/89516/what-trendiest-baby-name-american-history)

---

## Pattern 2 — Ashley Was a Boys' Name for 90 Years Before Becoming Almost Exclusively Female

**Finding:** Ashley was registered almost entirely for males from 1880 through the 1950s.
The 1960s saw the first meaningful crossover; by the 1980s it had become **98% female**
(352,137 female vs 5,212 male in that single decade), and by the 2000s male use had
virtually disappeared (655 male births vs 132,977 female).

**Query that reveals it:**
```sql
SELECT (Year/10)*10 AS Decade, Gender, SUM(Count) AS Count
FROM national_names
WHERE Name = 'Ashley'
GROUP BY Decade, Gender
ORDER BY Decade
```

*To visualise: enter "Ashley" in Tab A with Gender = "Both" to see the crossover clearly.*

**Interpretation:** Ashley derives from an English surname meaning "ash-tree meadow" and
was traditionally a masculine given name in the UK and US. The crossover likely accelerated
after the soap opera *The Young and the Restless* introduced a prominent female character
named Ashley Abbott in 1982 — coinciding exactly with the decade of maximum female adoption
in the data. This is a well-documented sociolinguistic phenomenon: once a name begins to be
perceived as feminine, male parents rapidly abandon it (fearing social stigma for their
sons), which further accelerates the female association in a self-reinforcing loop. The
result is a near-complete gender migration accomplished within roughly two decades.
[[source]](https://en.wikipedia.org/wiki/Ashley_(given_name))

---

## Pattern 3 — The Top 10 Names Went From 22% of All Births to Just 5% in 130 Years

**Finding:** In the 1880s, the 10 most popular names accounted for **22.4%** of all
recorded births. By the 2000s that share had collapsed to **5.9%**, and by 2010 to **5.1%**
— meaning parents today are more than four times less likely to choose a top-10 name than
parents in the Victorian era.

**Query that reveals it:**
```sql
SELECT Decade, TotalBirths, Top10Births,
       ROUND(Top10Births * 100.0 / TotalBirths, 2) AS Top10Pct
FROM (
  SELECT (Year/10)*10 AS Decade, SUM(Count) AS TotalBirths
  FROM national_names GROUP BY (Year/10)*10
) total
JOIN (
  SELECT (Year/10)*10 AS Decade, SUM(Count) AS Top10Births
  FROM (
    SELECT Year, Name, SUM(Count) AS Count,
           ROW_NUMBER() OVER (PARTITION BY Year ORDER BY SUM(Count) DESC) AS rn
    FROM national_names GROUP BY Year, Name
  )
  WHERE rn <= 10
  GROUP BY (Year/10)*10
) top10 USING (Decade)
ORDER BY Decade
```

*To visualise: run the "Name diversity per year" example in Tab B → Line chart.*

**Interpretation:** The dramatic decline in naming concentration reflects a broad cultural
shift from conformity to individualism across the 20th century. In the 19th century, names
were heavily constrained by religious tradition (John, Mary, James, Elizabeth — all biblical)
and the expectation of naming children after relatives. The post-1960s explosion in unique
names coincides with the counterculture movement, mass immigration bringing non-Anglo names
into the mainstream, the rise of celebrity culture (parents naming children after pop stars
and athletes), and the internet era enabling parents to discover and invent names globally.
Interestingly, the share begins declining as early as the 1950s, suggesting the shift toward
individualism in naming predates the 1960s cultural revolution by at least a decade.
[[source]](https://www.bbc.com/culture/article/20160325-why-your-name-might-determine-your-destiny)

---

## Interesting Findings (Summary)

| # | Pattern | Key number |
|---|---|---|
| 1 | Two 1930s films + a #1 hit song + the Baby Boom compounded into Linda's all-time record spike | +47,072 births in a single year (1946→1947) |
| 2 | A 1982 soap opera character named Ashley Abbott triggered a self-reinforcing gender flip — once perceived as female, male parents abandoned it within a decade | 1880–1950: male; 1980s: 352k female vs 5k male |
| 3 | Shift from religious/family naming tradition to individualism, celebrity culture, and mass immigration drove a 4× collapse in naming conformity | 1880s: 22.4% → 2010s: 5.1% |
