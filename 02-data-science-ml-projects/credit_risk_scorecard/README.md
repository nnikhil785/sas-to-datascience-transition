# Credit Risk Scorecard (Logistic Regression + Gradient Boosting)

An end-to-end credit-risk model on synthetic account-level data: a
traditional **points-based scorecard** (the interpretable deliverable
underwriting and risk teams actually use) built alongside a gradient
boosting model for comparison.

This mirrors real scorecard-development and underwriting-strategy work
(credit-limit and delinquency scorecard development, new-account
performance analysis against origination criteria) — rebuilt end-to-end
in Python since production bank data can't be shared publicly.

## Data

Fully synthetic, generated in-script (`generate_data()`): 8,000 accounts
with credit score, utilization, DTI, delinquency history, tenure, and
income, with a 12-month default outcome simulated from a realistic
logistic risk function. No proprietary or customer data is used.

## What it does

1. Trains a logistic regression and a gradient boosting classifier to
   predict 12-month default.
2. Converts the logistic regression into a classic **points-based
   scorecard** (base score + points per variable bin), the standard
   presentation format for underwriting and business stakeholders.
3. Evaluates both models with ROC/AUC.
4. Saves feature importance and ROC curve plots.

## Running

```bash
pip install pandas numpy scikit-learn matplotlib
python credit_risk_model.py
```

## Outputs

- `scorecard.csv` — points by variable and bin
- `feature_importance.png` — gradient boosting feature importances
- `roc_curve.png` — ROC curves for both models

## Results (synthetic data)

| Model | AUC |
|---|---|
| Logistic Regression | ~0.76 |
| Gradient Boosting | ~0.75 |

The scorecard is directionally sensible: higher credit score and longer
tenure add points; higher utilization, DTI, and delinquency history
subtract points — the same monotonic relationships expected in a real
production scorecard.
