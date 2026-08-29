"""
Generates a small synthetic "customer_accounts" table with mixed data types
(numeric, categorical, date, and deliberately-missing values) so the
profiling / data-dictionary tools have something realistic to describe.
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(7)
N = 500


def generate() -> pd.DataFrame:
    df = pd.DataFrame({
        "customer_id": [f"CUST{i:05d}" for i in range(N)],
        "account_open_date": pd.to_datetime("2018-01-01") + pd.to_timedelta(
            RNG.integers(0, 365 * 6, N), unit="D"
        ),
        "credit_score": RNG.integers(500, 850, N).astype(float),
        "annual_income": RNG.normal(65000, 22000, N).round(2),
        "product_type": RNG.choice(["Credit Card", "Auto Loan", "Mortgage", "Student Loan"], N),
        "state": RNG.choice(["TX", "CA", "IA", "NY", "MI"], N),
        "is_delinquent": RNG.choice([0, 1], N, p=[0.92, 0.08]),
    })

    # Inject realistic missingness
    missing_income_idx = RNG.choice(N, size=int(N * 0.04), replace=False)
    df.loc[missing_income_idx, "annual_income"] = np.nan
    missing_score_idx = RNG.choice(N, size=int(N * 0.02), replace=False)
    df.loc[missing_score_idx, "credit_score"] = np.nan

    return df


if __name__ == "__main__":
    df = generate()
    out_path = __file__.rsplit("/", 1)[0] + "/customer_accounts.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df):,} rows to {out_path}")
