"""
Builds a small SQLite database (portfolio.db) populated with synthetic
consumer-lending data, so the analytical queries in analytical_queries.sql
can be run and verified by anyone cloning this repo -- no external
database server required.

Run:
    python setup_sqlite_db.py
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "portfolio.db"
RNG = np.random.default_rng(99)

N_ACCOUNTS = 800
PRODUCTS = ["Credit Card", "Auto Loan", "Mortgage", "Student Loan"]
BUCKETS = ["Current", "30DPD", "60DPD", "90DPD", "ChargeOff"]
BUCKET_TRANSITIONS = {
    "Current":   {"Current": 0.93, "30DPD": 0.07},
    "30DPD":     {"Current": 0.5, "30DPD": 0.2, "60DPD": 0.3},
    "60DPD":     {"Current": 0.2, "30DPD": 0.1, "60DPD": 0.2, "90DPD": 0.5},
    "90DPD":     {"Current": 0.1, "30DPD": 0.05, "60DPD": 0.1, "90DPD": 0.35, "ChargeOff": 0.4},
    "ChargeOff": {"ChargeOff": 1.0},
}


def next_bucket(bucket: str) -> str:
    probs = BUCKET_TRANSITIONS[bucket]
    return RNG.choice(list(probs.keys()), p=list(probs.values()))


def build_accounts() -> pd.DataFrame:
    return pd.DataFrame({
        "account_id": [f"ACCT{i:05d}" for i in range(N_ACCOUNTS)],
        "product_type": RNG.choice(PRODUCTS, N_ACCOUNTS),
        "origination_date": pd.to_datetime("2015-01-01")
        + pd.to_timedelta(RNG.integers(0, 365 * 8, N_ACCOUNTS), unit="D"),
        "credit_limit": RNG.uniform(1000, 30000, N_ACCOUNTS).round(2),
    })


def build_snapshots(accounts: pd.DataFrame, months: list[str]) -> pd.DataFrame:
    rows = []
    bucket = dict.fromkeys(accounts["account_id"], "Current")
    balance = dict(zip(accounts["account_id"], RNG.uniform(200, 15000, N_ACCOUNTS)))

    for month in months:
        for acct in accounts["account_id"]:
            rows.append((acct, month, round(balance[acct], 2), bucket[acct]))
            bucket[acct] = next_bucket(bucket[acct])
            if bucket[acct] != "ChargeOff":
                balance[acct] = max(0, balance[acct] * RNG.uniform(0.85, 1.05))

    return pd.DataFrame(rows, columns=["account_id", "snapshot_month", "balance", "delinquency_bucket"])


def main() -> None:
    accounts = build_accounts()
    months = [f"2025-{m:02d}" for m in range(1, 13)]
    snapshots = build_snapshots(accounts, months)

    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    schema_sql = (HERE / "schema.sql").read_text()
    conn.executescript(schema_sql)

    accounts.to_sql("accounts", conn, if_exists="append", index=False)
    snapshots.to_sql("account_month_snapshot", conn, if_exists="append", index=False)
    conn.commit()

    n_accounts = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    n_snapshots = conn.execute("SELECT COUNT(*) FROM account_month_snapshot").fetchone()[0]
    conn.close()

    print(f"Built {DB_PATH.name}: {n_accounts:,} accounts, {n_snapshots:,} monthly snapshots")


if __name__ == "__main__":
    main()
