# SAS → Python/R Migration Examples

Side-by-side rebuilds of real analytics patterns from 12 years of
production SAS/SQL work — each example implements identical logic in
SAS, Python, and (where applicable) R, so the migration is demonstrated
directly rather than just claimed.

| Project | What it shows |
|---|---|
| [`delinquency_roll_rate_analysis/`](delinquency_roll_rate_analysis/) | Month-over-month delinquency-bucket transition ("roll-rate") report — self-joins, PROC FREQ, and row-percentage calculations, in SAS, Python, and R |
| [`data_profiling_dictionary/`](data_profiling_dictionary/) | Reusable data-dictionary / profiling tool — PROC CONTENTS/MEANS macro vs. a generic pandas profiling function |

Both projects include a synthetic data generator so every non-SAS script
is independently runnable.
