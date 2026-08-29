"""
Generates a synthetic credit-card account-month delinquency dataset.

This mirrors the shape of the real account/transaction/bureau data used in
production roll-rate analysis (Wells Fargo / USAA consumer banking work),
but is entirely synthetic -- no proprietary or customer data is used
anywhere in this repository.

Output: account_month_delinquency.csv
Columns:
    account_id        - unique account identifier
    month             - integer month index (1-12)
    delinquency_bucket- one of: Current, 30DPD, 60DPD, 90DPD, ChargeOff
    balance           - outstanding balance for that account-month
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(seed=42)

N_ACCOUNTS = 2000
N_MONTHS = 12

BUCKETS = ["Current", "30DPD", "60DPD", "90DPD", "ChargeOff"]
BUCKET_ORDER = {b: i for i, b in enumerate(BUCKETS)}

# Transition probabilities: rows = current bucket, cols = next bucket
# Mimics realistic roll-rate behavior: most accounts stay current or cure,
# a minority roll forward into deeper delinquency.
TRANSITIONS = {
    "Current":   {"Current": 0.94, "30DPD": 0.06, "60DPD": 0.00, "90DPD": 0.00, "ChargeOff": 0.00},
    "30DPD":     {"Current": 0.45, "30DPD": 0.20, "60DPD": 0.35, "90DPD": 0.00, "ChargeOff": 0.00},
    "60DPD":     {"Current": 0.20, "30DPD": 0.10, "60DPD": 0.20, "90DPD": 0.50, "ChargeOff": 0.00},
    "90DPD":     {"Current": 0.10, "30DPD": 0.05, "60DPD": 0.10, "90DPD": 0.35, "ChargeOff": 0.40},
    "ChargeOff": {"Current": 0.00, "30DPD": 0.00, "60DPD": 0.00, "90DPD": 0.00, "ChargeOff": 1.00},
}


def next_bucket(current: str) -> str:
    probs = TRANSITIONS[current]
    return RNG.choice(list(probs.keys()), p=list(probs.values()))


def generate() -> pd.DataFrame:
    rows = []
    starting_bucket = RNG.choice(BUCKETS, size=N_ACCOUNTS, p=[0.90, 0.06, 0.02, 0.01, 0.01])
    balances = RNG.uniform(200, 15000, size=N_ACCOUNTS)

    current_bucket = dict(zip(range(N_ACCOUNTS), starting_bucket))
    current_balance = dict(zip(range(N_ACCOUNTS), balances))

    for month in range(1, N_MONTHS + 1):
        for acct in range(N_ACCOUNTS):
            bucket = current_bucket[acct]
            balance = current_balance[acct]
            rows.append((f"ACCT{acct:05d}", month, bucket, round(balance, 2)))
            new_bucket = next_bucket(bucket)
            current_bucket[acct] = new_bucket
            if new_bucket == "ChargeOff":
                current_balance[acct] = balance  # frozen at charge-off
            else:
                current_balance[acct] = max(0, balance * RNG.uniform(0.85, 1.05))

    return pd.DataFrame(rows, columns=["account_id", "month", "delinquency_bucket", "balance"])


if __name__ == "__main__":
    df = generate()
    out_path = __file__.rsplit("/", 1)[0] + "/account_month_delinquency.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df):,} rows to {out_path}")
    print(df.head())
