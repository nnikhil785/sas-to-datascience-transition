# Delinquency Roll-Rate Analysis: SAS → Python → R

A side-by-side migration of a classic consumer-credit **roll-rate analysis**
— the month-over-month delinquency-bucket transition report used to monitor
30/60/90-day-past-due trends and charge-off risk (the same analysis pattern
referenced throughout the author's Wells Fargo / USAA experience).

All three versions implement identical logic and produce identical output:

1. Load account-month delinquency data.
2. Self-join each account's bucket in month *N* to its bucket in month *N+1*.
3. Build a `bucket_from x bucket_to` transition matrix (counts).
4. Convert counts to row-percentages (the actual "roll rate").
5. Report the headline "Current → Any Delinquency" roll rate.

## Why this project

This is the exact kind of report built and maintained in production SAS
environments for portfolio risk monitoring. Showing the same logic in SAS,
Python (pandas), and R side-by-side demonstrates the SAS→Python/R migration
skill directly, rather than just claiming it.

## Data

`data/generate_synthetic_data.py` generates a fully synthetic 2,000-account,
12-month account-level dataset with realistic transition probabilities. No
proprietary, customer, or production data is used anywhere in this repo.

```bash
python data/generate_synthetic_data.py
```

## Running each version

```bash
# Python
python python/roll_rate_analysis.py

# R
Rscript r/roll_rate_analysis.R

# SAS (sas/roll_rate_analysis.sas) is illustrative -- written in
# production SAS syntax (PROC SQL, PROC FREQ, PROC REPORT) but requires a
# licensed SAS environment and a LIBNAME pointing at real data to execute.
```

## Migration notes

| SAS construct | Python (pandas) equivalent | R (base R) equivalent |
|---|---|---|
| `PROC SQL` self-join | `DataFrame.merge()` | `merge()` |
| `PROC FREQ` two-way table | `pandas.crosstab()` | `table()` |
| Row-percent calculation | `.div(rowsum, axis=0)` | `prop.table(x, margin = 1)` |
| `PROC REPORT` | `DataFrame.to_string()` / plotting | `print()` / `ggplot2` |
