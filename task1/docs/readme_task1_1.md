# Task 1.1 – Data Loading & Schema Design

## What I Built and How It Works

I built a reproducible data pipeline (Jupyter notebook `task1_baby_names.ipynb`) that:

1. **Reads** two CSV files from the official US Social Security Administration baby-names dataset:
   - `NationalNames.csv` (~1.8 million rows, aggregated US counts per name/year/gender)
   - `StateNames.csv` (~5.6 million rows, same data broken down by US state)

2. **Creates a SQLite database** (`baby_names.db`) with two tables — `national_names` and
   `state_names` — whose schemas match the CSV columns exactly, with appropriate SQL types
   for each column.

3. **Loads the data** in 50 000-row chunks using pandas `read_csv(chunksize=...)` and
   `DataFrame.to_sql(if_exists='append')`. Chunked loading keeps memory usage flat regardless
   of file size, which matters for the 148 MB StateNames file.

4. **Creates indexes** and verifies their effectiveness via `EXPLAIN QUERY PLAN` and a
   timed benchmark that drops/restores the name index to measure the speedup directly.

---

## Technologies & Libraries

| Technology | Why chosen |
|---|---|
| **SQLite / sqlite3** | Required by the assignment. Zero-dependency, file-based, ships with Python. |
| **pandas** | `read_csv(chunksize=...)` provides memory-efficient streaming; `to_sql` handles type inference and bulk inserts cleanly. |
| **Jupyter Notebook** | Enables mixed code + markdown in a single file, ideal for embedding index-justification prose alongside the code that creates them. Easy to upload to Google Colab. |
| **Python `time` module** | Lightweight benchmarking without extra dependencies. |

SQLite was the natural fit here — the dataset fits comfortably in a single file (~300 MB on
disk after indexing), queries are local and fast, and there is no need for a server process.

---

## Challenges & Solutions

**1. Loading the 148 MB StateNames.csv without running out of memory**
Reading the whole file into a DataFrame at once would use ~1 GB of RAM after type conversion.
Solution: `pd.read_csv(chunksize=50_000)` streams the file in batches; each batch is inserted
and then garbage-collected.

**2. Slow bulk insert into SQLite**
Default SQLite settings issue an `fsync` after every transaction, making millions of inserts
very slow. Solution: Set `PRAGMA synchronous = OFF` and `PRAGMA journal_mode = MEMORY`
during the load, then restore safe defaults. This gave a ~10× speedup on the StateNames load.

**3. Ensuring the notebook is fully reproducible**
If `baby_names.db` already existed from a previous run, re-running the notebook would
duplicate rows. Solution: Delete the DB file at the start of the notebook before creating
fresh tables.

---

## Interesting Findings

**Index speedup is dramatic at this scale.** The benchmark in the notebook shows that a
`WHERE Name = 'Emma'` query on 1.8 million rows drops from ~150–200 ms (full table scan)
to ~2–5 ms (index seek) — roughly a **50–80× speedup**. This confirms that indexing is not
optional for an interactive app: without the Name index, every keystroke in the name-search
box would trigger a half-second database stall.

**The composite `(Name, Year)` index acts as a covering index** for the relative-popularity
query (`WHERE Name = ? AND Year = ?`). SQLite's `EXPLAIN QUERY PLAN` output changes from
`SEARCH … USING INDEX idx_nat_name` (still needs table look-up for Count) to
`SEARCH … USING COVERING INDEX idx_nat_name_year` (all needed columns are in the index
itself), saving an extra level of I/O.

**Data spans 135 years (1880–2014)**, giving a rich longitudinal view of US naming culture
well-suited for the trend analysis in Task 1.3.
