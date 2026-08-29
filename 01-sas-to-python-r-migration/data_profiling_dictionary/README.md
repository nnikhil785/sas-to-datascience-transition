# Automated Data Profiling / Data Dictionary: SAS → Python

A migration of a reusable **data-dictionary generator** — the kind of tool
used to profile and document datasets ahead of audits, migrations, or
modeling work (referenced throughout the author's DAQC and SAS-to-cloud
migration-readiness experience).

Both versions produce the same output for any dataset: variable name,
type, missing count/%, distinct-value count, and (for numeric columns)
min/mean/max.

## Why this project

Profiling and documenting datasets is one of the most repeated tasks in
data governance and migration work. The SAS version needs a hand-rolled
macro with a per-variable loop for distinct counts; the Python version
does the same job in ~20 lines using `nunique()`, generically for any
DataFrame — a concrete example of what improves when this workflow moves
off SAS.

## Data

`data/generate_sample_data.py` creates a small synthetic customer-accounts
table with realistic mixed types and injected missing values.

```bash
python data/generate_sample_data.py
```

## Running

```bash
# Python
python python/data_profiling.py

# SAS (sas/data_profiling_macro.sas) is illustrative production SAS syntax
# (PROC CONTENTS, PROC MEANS, PROC TRANSPOSE, PROC SQL) and requires a
# licensed SAS environment to execute.
```

## Migration notes

| SAS construct | Python (pandas) equivalent |
|---|---|
| `PROC CONTENTS` | `df.dtypes` |
| `PROC MEANS ... NMISS` | `series.isna().sum()` |
| Per-variable `PROC SQL COUNT(DISTINCT ...)` loop | `series.nunique()` (no macro loop needed) |
| `PROC TRANSPOSE` | not needed — pandas builds the dictionary row-wise directly |
