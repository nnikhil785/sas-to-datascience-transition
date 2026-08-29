"""
Time-Series Forecasting: Portfolio Delinquency Rate

Forecasts a monthly portfolio delinquency rate using Holt-Winters
exponential smoothing (trend + seasonality), the natural next step
beyond the trend *reporting* already represented elsewhere in this repo
(e.g. the roll-rate analysis in 01-sas-to-python-r-migration/) --
here the goal is an actual forward-looking forecast with an uncertainty
band, evaluated against a naive baseline the way a stakeholder would
expect it to be justified.

Workflow:
  1. Train/test split (holds out the last 12 months) to evaluate the
     model honestly on data it never saw.
  2. Seasonal decomposition, to show the trend/seasonal/residual
     components the model needs to capture.
  3. Two baselines for comparison:
       - naive-seasonal (this month's forecast = same month last year)
       - Holt-Winters (additive trend + additive seasonality)
     scored on the held-out 12 months with MAE / RMSE / MAPE.
  4. A final production-style forecast: refit Holt-Winters on the FULL
     history and forecast 6 months forward with a 95% confidence band.

Run:
    python forecast_model.py

Outputs (written next to this script):
    decomposition.png
    backtest_actual_vs_forecast.png
    future_forecast.png
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / "data" / "portfolio_delinquency_monthly.csv"
TEST_MONTHS = 12
FORECAST_HORIZON = 6


def load_series() -> pd.Series:
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    series = df.set_index("date")["delinquency_rate"]
    series = series.asfreq("MS")
    return series


def naive_seasonal_forecast(train: pd.Series, n_periods: int) -> np.ndarray:
    """Forecast = the value from the same calendar month one year earlier."""
    last_year = train.iloc[-12:]
    return np.array([last_year.iloc[i % 12] for i in range(n_periods)])


def score(actual: np.ndarray, predicted: np.ndarray) -> dict:
    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    mape = np.mean(np.abs((actual - predicted) / actual)) * 100
    return {"MAE": mae, "RMSE": rmse, "MAPE": mape}


def main() -> None:
    series = load_series()
    print(f"Loaded {len(series)} months: {series.index.min().date()} to {series.index.max().date()}\n")

    # --- Seasonal decomposition (on full history) ---
    decomposition = seasonal_decompose(series, model="additive", period=12)
    fig = decomposition.plot()
    fig.set_size_inches(8, 7)
    fig.suptitle("Portfolio Delinquency Rate -- Seasonal Decomposition", y=1.02)
    fig.tight_layout()
    fig.savefig(HERE / "decomposition.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # --- Train/test split ---
    train, test = series.iloc[:-TEST_MONTHS], series.iloc[-TEST_MONTHS:]
    print(f"Train: {len(train)} months, Test (held out): {len(test)} months\n")

    # --- Baseline: naive seasonal ---
    naive_pred = naive_seasonal_forecast(train, TEST_MONTHS)
    naive_scores = score(test.values, naive_pred)

    # --- Model: Holt-Winters (additive trend + additive seasonality) ---
    hw_model = ExponentialSmoothing(
        train, trend="add", seasonal="add", seasonal_periods=12
    ).fit()
    hw_pred = hw_model.forecast(TEST_MONTHS)
    hw_scores = score(test.values, hw_pred.values)

    print("Backtest on held-out 12 months:")
    print(f"  Naive-seasonal  -- MAE: {naive_scores['MAE']:.3f}  RMSE: {naive_scores['RMSE']:.3f}  MAPE: {naive_scores['MAPE']:.1f}%")
    print(f"  Holt-Winters    -- MAE: {hw_scores['MAE']:.3f}  RMSE: {hw_scores['RMSE']:.3f}  MAPE: {hw_scores['MAPE']:.1f}%")
    improvement = (1 - hw_scores["MAPE"] / naive_scores["MAPE"]) * 100
    print(f"  Holt-Winters reduces MAPE vs. naive-seasonal by {improvement:.0f}%\n")

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(train.index, train.values, label="Train (actual)", color="#1F3864")
    ax.plot(test.index, test.values, label="Test (actual)", color="#1F3864", linestyle="-", marker="o", markersize=4)
    ax.plot(test.index, naive_pred, label="Naive-seasonal forecast", color="#C0504D", linestyle="--")
    ax.plot(test.index, hw_pred.values, label="Holt-Winters forecast", color="#2E8B57", linestyle="--", marker="s", markersize=4)
    ax.set_ylabel("Delinquency Rate (%)")
    ax.set_title("Backtest: Actual vs. Forecast (last 12 months held out)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(HERE / "backtest_actual_vs_forecast.png", dpi=150)
    plt.close(fig)

    # --- Final forecast: refit on full history, forecast forward with CI ---
    final_model = ExponentialSmoothing(
        series, trend="add", seasonal="add", seasonal_periods=12
    ).fit()
    future_index = pd.date_range(
        series.index[-1] + pd.DateOffset(months=1), periods=FORECAST_HORIZON, freq="MS"
    )
    future_forecast = final_model.forecast(FORECAST_HORIZON)

    # Approximate 95% CI from in-sample residual std (a practical approach
    # when a model's built-in simulation/CI method isn't used).
    resid_std = np.std(final_model.resid)
    ci_half_width = 1.96 * resid_std * np.sqrt(1 + np.arange(1, FORECAST_HORIZON + 1) / 12)
    ci_low = future_forecast.values - ci_half_width
    ci_high = future_forecast.values + ci_half_width

    print(f"Forecast for the next {FORECAST_HORIZON} months (full history, with 95% CI):")
    for d, f, lo, hi in zip(future_index, future_forecast.values, ci_low, ci_high):
        print(f"  {d.date()}: {f:.2f}%  (95% CI: {lo:.2f}% - {hi:.2f}%)")

    fig, ax = plt.subplots(figsize=(9, 5))
    recent = series.iloc[-24:]
    ax.plot(recent.index, recent.values, label="Actual (last 24 months)", color="#1F3864")
    ax.plot(future_index, future_forecast.values, label="Forecast (next 6 months)", color="#2E8B57", marker="s", markersize=4)
    ax.fill_between(future_index, ci_low, ci_high, color="#2E8B57", alpha=0.2, label="95% CI")
    ax.set_ylabel("Delinquency Rate (%)")
    ax.set_title("Portfolio Delinquency Rate: 6-Month Forecast")
    ax.legend()
    fig.tight_layout()
    fig.savefig(HERE / "future_forecast.png", dpi=150)
    plt.close(fig)

    print(f"\nPlots written to {HERE}")


if __name__ == "__main__":
    main()
