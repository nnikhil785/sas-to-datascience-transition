# Data Quality Agent

Automates the kind of **Data Analytics Quality Control (DAQC)** review
referenced throughout the resume: checks a dataset against configurable
rules and produces a pass/fail scorecard plus a plain-English narrative
— the automation layer on top of manual DAQC review work.

## Two modes

- **Rule-based (default, no API key needed):** applies missingness,
  uniqueness, range, and allowed-value checks from a JSON rules file, and
  generates a templated narrative summary from the results.
- **AI narrative mode (`--ai`):** if `ANTHROPIC_API_KEY` is set and `pip
  install anthropic` has been run, sends the same rule-based scorecard to
  Claude to write a sharper, stakeholder-ready narrative — the AI is
  restricted to narrating the deterministic check results, never
  inventing new issues or numbers.

## Rules file format

```json
{
  "max_missing_pct": 3.0,
  "required_columns": ["customer_id", "credit_score"],
  "unique_columns": ["customer_id"],
  "range_checks": {"credit_score": [300, 850]},
  "allowed_values": {"state": ["TX", "CA", "IA", "NY", "MI"]}
}
```

## Running

```bash
pip install pandas anthropic   # anthropic only needed for --ai mode
python dq_agent.py ../../01-sas-to-python-r-migration/data_profiling_dictionary/data/customer_accounts.csv --rules example_rules.json
```

## Example output

Run against the synthetic `customer_accounts.csv` (which has a
deliberately-injected 4% missing rate on `annual_income` against a 3%
threshold), the agent correctly flags exactly that one issue and passes
everything else — 14 of 15 checks pass, and the one failure is reported
with the exact missingness percentage and threshold.
