"""
Roll-Rate Analysis - Python (pandas) migration of roll_rate_analysis.sas

Same business logic as the SAS version:
  1. Load account-month delinquency data.
  2. Self-join each account's bucket in month N to its bucket in month N+1.
  3. Build a bucket_from x bucket_to transition (roll-rate) matrix.
  4. Convert counts to row-percentages.
  5. Print a report-style summary.

Run:
    python roll_rate_analysis.py
"""
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "account_month_delinquency.csv"

BUCKET_ORDER = ["Current", "30DPD", "60DPD", "90DPD", "ChargeOff"]


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["delinquency_bucket"] = pd.Categorical(
        df["delinquency_bucket"], categories=BUCKET_ORDER, ordered=True
    )
    return df


def build_roll_pairs(df: pd.DataFrame) -> pd.DataFrame:
    """SAS step 2 (self-join on account_id where month_to = month_from + 1)."""
    left = df.rename(columns={"month": "month_from", "delinquency_bucket": "bucket_from"})
    right = df.rename(columns={"month": "month_to", "delinquency_bucket": "bucket_to"})
    right = right.assign(month_from=right["month_to"] - 1)

    pairs = left.merge(
        right[["account_id", "month_from", "bucket_to"]],
        on=["account_id", "month_from"],
        how="inner",
    )
    return pairs[["account_id", "month_from", "bucket_from", "bucket_to"]]


def build_roll_rate_matrix(pairs: pd.DataFrame) -> pd.DataFrame:
    """SAS steps 3-4 (PROC FREQ two-way table -> row percentages)."""
    counts = pd.crosstab(pairs["bucket_from"], pairs["bucket_to"])
    counts = counts.reindex(index=BUCKET_ORDER, columns=BUCKET_ORDER, fill_value=0)
    row_pct = counts.div(counts.sum(axis=1), axis=0).fillna(0)
    return counts, row_pct


def print_report(counts: pd.DataFrame, row_pct: pd.DataFrame) -> None:
    print("Roll-Rate Matrix - Account Counts (rows = From, cols = To)")
    print(counts.to_string())
    print()
    print("Roll-Rate Matrix - Row Percentages")
    print((row_pct * 100).round(1).to_string())
    print()
    # Headline risk metric analogous to what would go in a weekly report
    current_to_worse = row_pct.loc["Current", ["30DPD", "60DPD", "90DPD", "ChargeOff"]].sum()
    print(f"Current -> Any Delinquency roll rate: {current_to_worse:.2%}")


def main() -> None:
    df = load_data()
    pairs = build_roll_pairs(df)
    counts, row_pct = build_roll_rate_matrix(pairs)
    print_report(counts, row_pct)


if __name__ == "__main__":
    main()
