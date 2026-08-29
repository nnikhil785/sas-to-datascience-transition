"""
Automated Data Profiling / Data Dictionary tool - Python (pandas) migration
of data_profiling_macro.sas

Produces the same data-dictionary output as the SAS macro (name, type,
missing count/%, distinct count, plus numeric min/mean/max), but
generically for any pandas DataFrame -- no per-variable macro loop needed,
which is one of the concrete wins of moving this kind of work off SAS.

Run:
    python data_profiling.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "customer_accounts.csv"


def profile_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Equivalent of the SAS %profile_dataset macro, generalized to any df."""
    n_obs = len(df)
    rows = []

    for col in df.columns:
        series = df[col]
        n_missing = int(series.isna().sum())
        row = {
            "name": col,
            "dtype": str(series.dtype),
            "n_missing": n_missing,
            "pct_missing": round(n_missing / n_obs * 100, 1),
            "n_distinct": int(series.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(series):
            row.update({
                "min": series.min(),
                "mean": round(series.mean(), 2) if not series.isna().all() else np.nan,
                "max": series.max(),
            })
        else:
            row.update({"min": np.nan, "mean": np.nan, "max": np.nan})
        rows.append(row)

    return pd.DataFrame(rows)


def main() -> None:
    df = pd.read_csv(DATA_PATH, parse_dates=["account_open_date"])
    dictionary = profile_dataset(df)

    pd.set_option("display.width", 120)
    print(f"Data Dictionary for: {DATA_PATH.name}  ({len(df):,} rows, {len(df.columns)} columns)\n")
    print(dictionary.to_string(index=False))

    out_path = Path(__file__).resolve().parents[1] / "data" / "data_dictionary_output.csv"
    dictionary.to_csv(out_path, index=False)
    print(f"\nData dictionary written to {out_path}")


if __name__ == "__main__":
    main()
