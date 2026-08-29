# Customer Churn Prediction

A general applied-classification project — deliberately not tied to a
specific past employer (unlike the credit-risk and segmentation projects
in this repo) — built to demonstrate the full modeling workflow commonly
asked about in data scientist / analyst interviews: feature engineering,
a scikit-learn `Pipeline` with categorical encoding, model training, and a
complete evaluation suite.

## Data

Synthetic subscription-service data (tenure, monthly charges, contract
type, support calls, add-on services, autopay) with a churn outcome
simulated from a realistic risk function — contract type and support-call
volume are the dominant churn drivers, matching typical real-world churn
dynamics.

## What it does

1. Builds a `ColumnTransformer` + `RandomForestClassifier` pipeline.
2. Evaluates with precision/recall/F1 (classification report), ROC-AUC,
   and a confusion matrix.
3. Saves feature importance, confusion matrix, and ROC curve plots.

## Running

```bash
pip install pandas numpy scikit-learn matplotlib
python churn_model.py
```

## Outputs

- `confusion_matrix.png`
- `feature_importance.png`
- `roc_curve.png`

## Results (synthetic data)

AUC ≈ 0.69 — realistic for a churn model built on a handful of behavioral
features; contract type (month-to-month vs. annual) and support-call
volume are the strongest predictors, consistent with typical real-world
churn drivers.
