"""
Customer Segmentation via RFM + K-Means Clustering

Rebuilds the CRM behavioral-clustering work referenced on the resume
("analyzed customer spending patterns and purchase frequency to build
CRM clusters for customer segmentation" — Kellogg's, retail analytics
internal project) as a full, runnable pipeline: synthetic transaction
data -> RFM feature engineering -> K-Means -> named customer segments.

Run:
    python segmentation.py

Outputs (written next to this script):
    segment_profiles.csv   - mean RFM values and size per segment
    elbow_plot.png         - inertia vs. k, for choosing cluster count
    segment_scatter.png    - 2D visualization of segments (recency vs. monetary)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
RNG = np.random.default_rng(5)
N_CUSTOMERS = 1500


# --------------------------------------------------------------------------
# 1. Synthetic transaction data -> RFM features
# --------------------------------------------------------------------------
def generate_transactions() -> pd.DataFrame:
    """Simulates a year of retail transactions across distinct customer archetypes."""
    archetypes = RNG.choice(
        ["champion", "loyal", "at_risk", "new", "lapsed"],
        N_CUSTOMERS,
        p=[0.12, 0.28, 0.20, 0.15, 0.25],
    )
    rows = []
    today = pd.Timestamp("2025-12-31")

    params = {
        # (avg orders/year, avg order value, recency range in days)
        "champion": (24, 120, (1, 20)),
        "loyal": (12, 80, (5, 45)),
        "at_risk": (6, 90, (90, 200)),
        "new": (2, 60, (1, 30)),
        "lapsed": (3, 70, (200, 365)),
    }

    for cust_idx, archetype in enumerate(archetypes):
        n_orders_mean, aov_mean, recency_range = params[archetype]
        n_orders = max(1, RNG.poisson(n_orders_mean))
        last_purchase_days_ago = RNG.integers(*recency_range)

        for _ in range(n_orders):
            days_ago = RNG.integers(last_purchase_days_ago, 365)
            amount = max(5, RNG.normal(aov_mean, aov_mean * 0.35))
            rows.append({
                "customer_id": f"CUST{cust_idx:05d}",
                "transaction_date": today - pd.Timedelta(days=int(days_ago)),
                "amount": round(amount, 2),
                "archetype": archetype,  # kept for validation only, not used in modeling
            })

    return pd.DataFrame(rows)


def compute_rfm(transactions: pd.DataFrame, snapshot_date: pd.Timestamp) -> pd.DataFrame:
    grouped = transactions.groupby("customer_id").agg(
        recency=("transaction_date", lambda s: (snapshot_date - s.max()).days),
        frequency=("transaction_date", "count"),
        monetary=("amount", "sum"),
    )
    return grouped.reset_index()


# --------------------------------------------------------------------------
# 2. K-Means clustering
# --------------------------------------------------------------------------
def choose_k_via_elbow(X_scaled: np.ndarray, k_range=range(2, 9)) -> list[float]:
    inertias = []
    for k in k_range:
        km = KMeans(n_clusters=k, n_init=10, random_state=5)
        km.fit(X_scaled)
        inertias.append(km.inertia_)
    return inertias


def name_segments(profiles: pd.DataFrame) -> dict[int, str]:
    """
    Assigns human-readable names to clusters by ranking each on a composite
    RFM value score (higher frequency/monetary and lower recency = better),
    then mapping ranks onto standard CRM segment labels. Works for any
    cluster count by cycling through the label list if there are more
    clusters than named tiers.
    """
    monetary_rank = profiles["monetary"].rank(ascending=False)
    recency_rank = profiles["recency"].rank(ascending=True)  # rank 1 = most recent = best
    frequency_rank = profiles["frequency"].rank(ascending=False)

    composite_score = monetary_rank + recency_rank + frequency_rank  # lower = better segment
    ordered_clusters = composite_score.sort_values().index.tolist()

    tier_labels = ["Champions", "Loyal / Growing", "At Risk (was active)", "Lapsed / Low Value"]
    # If there are more clusters than labels, repeat the last label for the tail
    labels_for_clusters = tier_labels + [tier_labels[-1]] * max(0, len(ordered_clusters) - len(tier_labels))

    return {cluster_id: labels_for_clusters[i] for i, cluster_id in enumerate(ordered_clusters)}


def main() -> None:
    snapshot_date = pd.Timestamp("2026-01-01")
    transactions = generate_transactions()
    rfm = compute_rfm(transactions, snapshot_date)

    feature_cols = ["recency", "frequency", "monetary"]
    X = rfm[feature_cols].values
    X_scaled = StandardScaler().fit_transform(X)

    # Elbow plot to justify k
    inertias = choose_k_via_elbow(X_scaled)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(list(range(2, 9)), inertias, marker="o", color="#1F3864")
    ax.set_xlabel("k (number of clusters)")
    ax.set_ylabel("Inertia")
    ax.set_title("Elbow Plot — Choosing k for K-Means")
    fig.tight_layout()
    fig.savefig(HERE / "elbow_plot.png", dpi=150)
    plt.close(fig)

    # Fit final model (k=4 chosen from elbow inspection)
    K = 4
    km = KMeans(n_clusters=K, n_init=10, random_state=5)
    rfm["cluster"] = km.fit_predict(X_scaled)

    profiles = rfm.groupby("cluster")[feature_cols].mean().round(1)
    profiles["n_customers"] = rfm.groupby("cluster").size()
    segment_names = name_segments(profiles)
    profiles["segment_name"] = profiles.index.map(segment_names)
    rfm["segment_name"] = rfm["cluster"].map(segment_names)

    profiles.to_csv(HERE / "segment_profiles.csv")
    print(f"Segmented {len(rfm):,} customers into {K} clusters\n")
    print(profiles.to_string())

    # Scatter plot: recency vs monetary, colored by segment
    fig, ax = plt.subplots(figsize=(6, 5))
    for cluster_id, name in segment_names.items():
        subset = rfm[rfm["cluster"] == cluster_id]
        ax.scatter(subset["recency"], subset["monetary"], s=12, alpha=0.6, label=name)
    ax.set_xlabel("Recency (days since last purchase)")
    ax.set_ylabel("Monetary (total spend)")
    ax.set_title("Customer Segments — Recency vs. Monetary")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / "segment_scatter.png", dpi=150)
    plt.close(fig)

    print(f"\nOutputs written to {HERE}")


if __name__ == "__main__":
    main()
