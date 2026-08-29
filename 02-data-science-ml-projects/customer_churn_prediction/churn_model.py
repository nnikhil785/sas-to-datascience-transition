"""
Customer Churn Prediction - classification project

A general applied-ML project (not tied to a specific past employer,
unlike the credit-risk and segmentation projects in this repo) built to
demonstrate the classification/evaluation workflow requested by
Data Scientist / Analyst job postings: EDA-lite, feature engineering,
model training, and a full evaluation suite (precision/recall/F1/ROC-AUC,
confusion matrix, feature importance).

Data is synthetic, generated to resemble a typical subscription-service
churn dataset (tenure, charges, contract type, support calls, etc).

Run:
    python churn_model.py

Outputs (written next to this script):
    confusion_matrix.png
    feature_importance.png
    roc_curve.png
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (ConfusionMatrixDisplay, RocCurveDisplay,
                              classification_report, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

HERE = Path(__file__).resolve().parent
RNG = np.random.default_rng(23)
N = 5000


def generate_data(n: int = N) -> pd.DataFrame:
    tenure_months = RNG.integers(0, 72, n)
    contract = RNG.choice(["Month-to-month", "One year", "Two year"], n, p=[0.55, 0.25, 0.20])
    monthly_charges = RNG.normal(70, 25, n).clip(20, 150)
    support_calls = RNG.poisson(1.2, n)
    has_addon_services = RNG.integers(0, 4, n)
    payment_autopay = RNG.integers(0, 2, n)

    contract_risk = {"Month-to-month": 1.0, "One year": 0.35, "Two year": 0.1}
    contract_effect = np.array([contract_risk[c] for c in contract])

    logit = (
        -1.2
        + 1.6 * contract_effect
        + (-0.03) * tenure_months / 12
        + 0.015 * (monthly_charges - 70) / 25
        + 0.30 * support_calls
        + (-0.20) * has_addon_services
        + (-0.35) * payment_autopay
    )
    prob_churn = 1 / (1 + np.exp(-logit))
    churn = RNG.binomial(1, prob_churn)

    return pd.DataFrame({
        "tenure_months": tenure_months,
        "contract": contract,
        "monthly_charges": monthly_charges.round(2),
        "support_calls_6mo": support_calls,
        "addon_services": has_addon_services,
        "autopay": payment_autopay,
        "churned": churn,
    })


def main() -> None:
    df = generate_data()
    numeric_features = ["tenure_months", "monthly_charges", "support_calls_6mo",
                         "addon_services", "autopay"]
    categorical_features = ["contract"]

    X = df[numeric_features + categorical_features]
    y = df["churned"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=23, stratify=y
    )

    preprocess = ColumnTransformer([
        ("cat", OneHotEncoder(drop="first"), categorical_features),
    ], remainder="passthrough")

    model = Pipeline([
        ("preprocess", preprocess),
        ("clf", RandomForestClassifier(n_estimators=300, max_depth=6, random_state=23)),
    ])
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_proba)

    print(f"Dataset: {len(df):,} customers, churn rate = {y.mean():.2%}")
    print(f"\nTest AUC: {auc:.3f}\n")
    print(classification_report(y_test, y_pred, target_names=["Retained", "Churned"]))

    # Confusion matrix
    fig, ax = plt.subplots(figsize=(5, 5))
    ConfusionMatrixDisplay.from_predictions(
        y_test, y_pred, display_labels=["Retained", "Churned"], ax=ax, cmap="Blues"
    )
    ax.set_title("Confusion Matrix — Churn Prediction")
    fig.tight_layout()
    fig.savefig(HERE / "confusion_matrix.png", dpi=150)
    plt.close(fig)

    # ROC curve
    fig, ax = plt.subplots(figsize=(5, 5))
    RocCurveDisplay.from_predictions(y_test, y_proba, name="Random Forest", ax=ax)
    ax.set_title("ROC Curve — Churn Prediction")
    fig.tight_layout()
    fig.savefig(HERE / "roc_curve.png", dpi=150)
    plt.close(fig)

    # Feature importance (post-encoding names)
    feature_names = model.named_steps["preprocess"].get_feature_names_out()
    importances = pd.Series(
        model.named_steps["clf"].feature_importances_, index=feature_names
    ).sort_values()
    fig, ax = plt.subplots(figsize=(6, 4))
    importances.plot.barh(ax=ax, color="#1F3864")
    ax.set_title("Feature Importance — Churn Prediction")
    fig.tight_layout()
    fig.savefig(HERE / "feature_importance.png", dpi=150)
    plt.close(fig)

    print(f"\nPlots written to {HERE}")


if __name__ == "__main__":
    main()
