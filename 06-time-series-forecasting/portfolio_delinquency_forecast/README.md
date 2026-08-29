# Time-Series Forecasting: Portfolio Delinquency Rate

Forecasts a synthetic monthly portfolio delinquency rate using Holt-Winters
exponential smoothing, evaluated honestly against a naive-seasonal baseline
on a held-out test period, then used to produce a forward-looking 6-month
forecast with a confidence band.

## Why this project

The resume references "forecasting portfolio and cost trends," but the
rest of this repo only *reports* trends (roll-rate analysis, delinquency
rollups) — it never actually forecasts forward. This project closes that
gap with a real forecasting workflow: train/test split, a documented
baseline, an honest accuracy comparison, and a production-style forecast
with uncertainty, rather than a trend line extrapolated by eye.

## Data

Fully synthetic (`data/generate_synthetic_data.py`) — 66 months of a
portfolio delinquency rate with three deliberately-built components so
the decomposition step has something real to find:

- a slow upward **trend** (portfolio aging/seasoning over time)
- yearly **seasonality** (a Q1 delinquency bump, modeling post-holiday
  spending catching up with borrowers)
- random noise

## What it does (`forecast_model.py`)

1. **Seasonal decomposition** — splits the series into trend, seasonal,
   and residual components (`statsmodels.tsa.seasonal.seasonal_decompose`).
2. **Backtest** — holds out the last 12 months, then compares two
   forecasts on it:
   - **naive-seasonal baseline**: this month's forecast = the same
     calendar month one year ago (the standard baseline any real model
     has to beat)
   - **Holt-Winters** (additive trend + additive seasonality)
   scored with MAE, RMSE, and MAPE.
3. **Production forecast** — refits Holt-Winters on the *full* history
   and forecasts 6 months forward with an approximate 95% confidence
   band (derived from in-sample residual variance).

## Running

```bash
pip install -r ../../requirements.txt
python data/generate_synthetic_data.py   # writes data/portfolio_delinquency_monthly.csv
python forecast_model.py
```

Outputs three plots next to the script:

- `decomposition.png` — trend / seasonal / residual components
- `backtest_actual_vs_forecast.png` — actual vs. naive-seasonal vs.
  Holt-Winters on the held-out 12 months
- `future_forecast.png` — the 6-month forward forecast with 95% CI

## Example results

```
Backtest on held-out 12 months:
  Naive-seasonal  -- MAE: 0.239  RMSE: 0.291  MAPE: 5.8%
  Holt-Winters    -- MAE: 0.120  RMSE: 0.138  MAPE: 2.8%
  Holt-Winters reduces MAPE vs. naive-seasonal by 51%

Forecast for the next 6 months (full history, with 95% CI):
  2026-07-01: 4.27%  (95% CI: 3.98% - 4.57%)
  2026-08-01: 4.16%  (95% CI: 3.86% - 4.46%)
  2026-09-01: 3.84%  (95% CI: 3.53% - 4.15%)
  2026-10-01: 3.72%  (95% CI: 3.40% - 4.04%)
  2026-11-01: 3.96%  (95% CI: 3.63% - 4.29%)
  2026-12-01: 4.05%  (95% CI: 3.71% - 4.39%)
```

Data generation uses a fixed random seed, so these exact numbers reproduce
on every run.
