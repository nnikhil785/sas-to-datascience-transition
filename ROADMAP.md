# Roadmap

This repo is built and extended alongside an active SAS/SQL → Data
Science/ML career transition — new projects are added over time rather
than all at once, each one targeting a specific gap or skill relevant to
roles being applied for.

## In progress / next up

- [ ] **Time-series forecasting** — forecasting portfolio delinquency or
  utilization trend with `statsmodels`/Prophet. Builds directly on the
  "forecasting portfolio and cost trends" work already in
  `02-data-science-ml-projects/`, with a proper forecasting model behind
  it instead of trend reporting alone.

## Later

- [ ] **Model serving** — a small FastAPI service wrapping the credit
  risk model to serve predictions over an endpoint.
- [ ] **Interactive dashboard** — a Streamlit app over the segmentation
  or roll-rate data, as a Python-native complement to the Tableau/Power
  BI experience already on the resume.
- [ ] **Testing & CI** — `pytest` unit tests on one or two existing
  projects, plus a GitHub Actions workflow to run them on every push.
- [ ] **NLP/LLM project** — classifying or summarizing a synthetic
  support-ticket dataset.
- [ ] **Deep learning basics** — a PyTorch version of the churn or
  credit-risk model, for breadth alongside the classical ML already here.

## Completed

- [x] SAS → Python/R migration examples (roll-rate analysis, data
  profiling/dictionary generator)
- [x] Credit risk scorecard, churn prediction, customer segmentation
- [x] SQL analytics portfolio (window functions, CTEs) on SQLite
- [x] AI-agentic workflows (SAS macro documenter, data quality agent)
- [x] A/B testing & experimentation (`05-experimentation-and-causal-inference/`)
  — hypothesis testing, confidence intervals, and power/sample-size
  analysis on a synthetic checkout-conversion test, plus a peeking-bias
  simulation
