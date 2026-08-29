# SQL Analytics Portfolio

Advanced SQL — window functions, CTEs, and cohort-style analysis — run
against a small synthetic consumer-lending SQLite database, so every
query here is independently runnable and verifiable (not just written).

## Why SQLite

SQLite ships with Python and needs no server, so anyone cloning this repo
can run every query immediately. The SQL itself (window functions, CTEs)
is standard and translates directly to Teradata, Snowflake, Oracle, or
SQL Server — the platforms referenced throughout the resume.

## Setup

```bash
pip install pandas
python setup_sqlite_db.py   # builds portfolio.db from synthetic data
python run_queries.py       # runs every query in analytical_queries.sql and prints results
```

## Queries included (`analytical_queries.sql`)

1. **Month-over-month roll-rate matrix** — `LAG()` window function per
   account, the SQL-native equivalent of the self-join used in the SAS
   migration example in `01-sas-to-python-r-migration/`.
2. **Top-N accounts per product** — `RANK() ... PARTITION BY`, the
   classic "top-N per group" pattern.
3. **3-month moving average of portfolio balance** — `AVG() OVER (...
   ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`, used to smooth monthly
   financial/risk reporting trends.
4. **Origination-year cohort delinquency rate** — vintage/cohort analysis
   grouping accounts by origination year to compare delinquency rates
   across cohorts.

## Schema (`schema.sql`)

Two tables: `accounts` (static account attributes) and
`account_month_snapshot` (monthly balance + delinquency bucket per
account) — the same shape as the account-month data used in the roll-rate
migration project.
