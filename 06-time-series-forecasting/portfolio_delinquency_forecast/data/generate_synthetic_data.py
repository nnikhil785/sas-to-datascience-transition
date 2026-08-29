"""
Generates a synthetic monthly portfolio delinquency-rate time series with:
  - a slow upward trend (portfolio seasoning / aging)
  - yearly seasonality (post-holiday-spending delinquency bump each Q1)
  - realistic noise

Writes: portfolio_delinquency_monthly.csv (date, delinquency_rate,
total_accounts, delinquent_accounts)
"""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RNG = np.random.default_rng(7)

N_MONTHS = 66  # 5.5 years of monthly history


def main() -> None:
    dates = pd.date_range("2021-01-01", periods=N_MONTHS, freq="MS")
    t = np.arange(N_MONTHS)

    # Slow upward trend: portfolio aging pushes delinquency up gradually.
    trend = 3.2 + 0.018 * t

    # Yearly seasonality: delinquency rate peaks in Jan/Feb (post-holiday
    # spending catches up with borrowers), dips mid-year.
    month = dates.month
    seasonal = 0.55 * np.sin(2 * np.pi * (month - 2) / 12) + 0.25 * np.cos(
        2 * np.pi * (month - 2) / 12
    )

    noise = RNG.normal(0, 0.18, N_MONTHS)

    delinquency_rate = np.clip(trend + seasonal + noise, 0.5, None)

    # Portfolio size grows slowly too, so we can report raw account counts
    total_accounts = (12000 + 40 * t + RNG.normal(0, 60, N_MONTHS)).round().astype(int)
    delinquent_accounts = (total_accounts * delinquency_rate / 100).round().astype(int)

    df = pd.DataFrame(
        {
            "date": dates,
            "delinquency_rate": delinquency_rate.round(3),
            "total_accounts": total_accounts,
            "delinquent_accounts": delinquent_accounts,
        }
    )
    out_path = HERE / "portfolio_delinquency_monthly.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} monthly rows to {out_path}")
    print(df.head())
    print("...")
    print(df.tail())


if __name__ == "__main__":
    main()
