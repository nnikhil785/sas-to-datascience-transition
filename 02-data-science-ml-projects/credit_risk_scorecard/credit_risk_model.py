"""
Credit Risk Scorecard - logistic regression + gradient boosting

Builds a traditional credit-risk "scorecard" (points-based, interpretable)
alongside a gradient-boosted model, on synthetic account-level credit data.
This mirrors real scorecard-development work referenced on the resume
(credit-limit and delinquency scorecard development, underwriting strategy
analysis) -- rebuilt end-to-end in Python since production bank data can't
be shared.

Data is entirely synthetic (see generate_data()); no proprietary or
customer data is used.

Run:
    python credit_risk_model.py

Outputs (written next to this script):
    scorecard.csv           - points-based scorecard by variable bin
    feature_importance.png  - gradient boosting feature importances
    roc_curve.png           - ROC curves for both models
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import RocCurveDisplay, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
RNG = np.random.default_rng(11)
N = 8000


# --------------------------------------------------------------------------
# 1. Synthetic data generation
# --------------------------------------------------------------------------
def generate_data(n: int = N) -> pd.DataFrame:
    credit_score = RNG.normal(680, 60, n).clip(500, 850)
    utilization = RNG.beta(2, 5, n)  # skewed toward lower utilization
    dti = RNG.normal(0.32, 0.12, n).clip(0.02, 0.9)  # debt-to-income
    delinquencies_24mo = RNG.poisson(0.3, n)
    months_on_book = RNG.integers(1, 120, n)
    income = RNG.normal(62000, 24000, n).clip(15000, None)

    # True underlying default probability (logistic function of risk factors)
    logit = (
        -4.2
        + (-0.015) * (credit_score - 680)
        + 3.0 * utilization
        + 2.2 * dti
        + 0.55 * delinquencies_24mo
        + (-0.01) * (months_on_book / 12)
        + (-0.000006) * (income - 62000)
    )
    prob_default = 1 / (1 + np.exp(-logit))
    default_12mo = RNG.binomial(1, prob_default)

    return pd.DataFrame({
        "credit_score": credit_score.round(0),
        "utilization": utilization.round(3),
        "dti": dti.round(3),
        "delinquencies_24mo": delinquencies_24mo,
        "months_on_book": months_on_book,
        "income": income.round(2),
        "default_12mo": default_12mo,
    })


# --------------------------------------------------------------------------
# 2. Points-based scorecard (classic credit-risk deliverable)
# --------------------------------------------------------------------------
def build_scorecard(df: pd.DataFrame, model: LogisticRegression, scaler: StandardScaler,
                     feature_cols: list[str]) -> pd.DataFrame:
    """
    Converts logistic-regression coefficients into a WOE-style points
    scorecard: base_points + sum(variable_points). Uses simple quartile
    binning per variable for readability, the way a production scorecard
    would present risk drivers to underwriting/business stakeholders.
    """
    rows = []
    base_points = 600
    pdo = 40  # "points to double the odds", standard scorecard convention
    factor = pdo / np.log(2)

    coefs = dict(zip(feature_cols, model.coef_[0]))
    means = dict(zip(feature_cols, scaler.mean_))
    stds = dict(zip(feature_cols, scaler.scale_))

    for col in feature_cols:
        bins = pd.qcut(df[col], 4, duplicates="drop")
        for interval in sorted(bins.cat.categories, key=lambda i: i.left):
            mid = (interval.left + interval.right) / 2
            scaled_mid = (mid - means[col]) / stds[col]
            points = round(-coefs[col] * scaled_mid * factor / len(feature_cols))
            rows.append({
                "variable": col,
                "bin": str(interval),
                "points": int(points),
            })

    scorecard = pd.DataFrame(rows)
    header = pd.DataFrame([{"variable": "BASE_SCORE", "bin": "-", "points": base_points}])
    return pd.concat([header, scorecard], ignore_index=True)


# --------------------------------------------------------------------------
# 3. Modeling + evaluation
# --------------------------------------------------------------------------
def main() -> None:
    df = generate_data()
    feature_cols = ["credit_score", "utilization", "dti", "delinquencies_24mo",
                     "months_on_book", "income"]

    X = df[feature_cols]
    y = df["default_12mo"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=11, stratify=y
    )

    scaler = StandardScaler().fit(X_train)
    X_train_s = scaler.transform(X_train)
    X_test_s = scaler.transform(X_test)

    logreg = LogisticRegression(max_iter=1000)
    logreg.fit(X_train_s, y_train)
    logreg_auc = roc_auc_score(y_test, logreg.predict_proba(X_test_s)[:, 1])

    gbm = GradientBoostingClassifier(random_state=11)
    gbm.fit(X_train, y_train)
    gbm_auc = roc_auc_score(y_test, gbm.predict_proba(X_test)[:, 1])

    print(f"Dataset: {len(df):,} accounts, default rate = {y.mean():.2%}")
    print(f"Logistic Regression AUC: {logreg_auc:.3f}")
    print(f"Gradient Boosting AUC:   {gbm_auc:.3f}")

    # Scorecard
    scorecard = build_scorecard(df, logreg, scaler, feature_cols)
    scorecard.to_csv(HERE / "scorecard.csv", index=False)
    print(f"\nScorecard written to {HERE / 'scorecard.csv'}")
    print(scorecard.head(10).to_string(index=False))

    # Feature importance plot (GBM)
    importances = pd.Series(gbm.feature_importances_, index=feature_cols).sort_values()
    fig, ax = plt.subplots(figsize=(6, 4))
    importances.plot.barh(ax=ax, color="#1F3864")
    ax.set_title("Gradient Boosting Feature Importance — Credit Default Model")
    ax.set_xlabel("Importance")
    fig.tight_layout()
    fig.savefig(HERE / "feature_importance.png", dpi=150)
    plt.close(fig)

    # ROC curve plot
    fig, ax = plt.subplots(figsize=(5, 5))
    RocCurveDisplay.from_estimator(logreg, X_test_s, y_test, ax=ax, name="Logistic Regression")
    RocCurveDisplay.from_estimator(gbm, X_test, y_test, ax=ax, name="Gradient Boosting")
    ax.set_title("ROC Curve — Credit Default Prediction")
    fig.tight_layout()
    fig.savefig(HERE / "roc_curve.png", dpi=150)
    plt.close(fig)

    print(f"Plots written to {HERE / 'feature_importance.png'} and {HERE / 'roc_curve.png'}")


if __name__ == "__main__":
    main()
