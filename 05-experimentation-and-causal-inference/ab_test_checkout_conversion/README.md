# A/B Test Analysis: Checkout Conversion

A complete experimentation workflow on a synthetic checkout-conversion
test (control vs. a new checkout flow) — the kind of test behind
"optimize checkout conversion" work on consumer-lending/fintech risk &
analytics teams, and the most commonly requested skill on Data
Scientist / Analytics postings that this repo's other sections don't
yet cover.

## Why this project

Every other project in this repo answers "can you build a model / write
the SQL / migrate the SAS code" — but says nothing about experimentation,
which is a distinct and frequently-required skill: designing a valid
test, sizing it correctly, reading the result honestly, and knowing the
common ways teams fool themselves. This project demonstrates all four.

## What it does

1. **Pre-experiment power analysis** — given a baseline conversion rate
   and a minimum detectable effect (MDE), computes the sample size
   needed per arm for a properly powered test (`statsmodels`
   `NormalIndPower`).
2. **Hypothesis test on the result** — a two-proportion z-test
   (`proportions_ztest`) plus a 95% confidence interval on the lift
   (`confint_proportions_2indep`), not just a bare p-value.
3. **A "peeking" simulation** — simulates many experiments where control
   and treatment have the *same* true rate (the null is true), then
   compares the false-positive rate from checking significance every 100
   users and stopping early vs. looking once at a fixed sample size.
   This demonstrates, empirically, the single most common experimentation
   mistake: peeking inflates the false-positive rate well above the
   nominal 5% (checking every 100 users up to n=2,000 pushes it to
   roughly 20–30%, vs. ~5% for a single fixed-horizon look).

## Data

Fully synthetic and simulated in-script (`numpy` binomial draws) — no
external data file. Conversion rates and sample sizes are chosen to be
realistic for a consumer checkout flow.

## Running

```bash
pip install -r ../../requirements.txt
python ab_test_analysis.py
```

Outputs two plots next to the script:

- `conversion_by_arm.png` — conversion rate by arm with 95% CIs
- `peeking_simulation.png` — false-positive rate, peeking vs. fixed-N

## Example results

```
Pre-experiment power analysis:
  Baseline conversion: 10%, MDE: +2% (absolute)
  Required sample size per arm (alpha=0.05, power=0.80): 3,835

Experiment results (single fixed-horizon analysis):
  Control conversion:   10.30%  (n=3,835)
  Treatment conversion: 12.75%  (n=3,835)
  Absolute lift: +2.45%
  95% CI on lift: [+1.02%, +3.88%]
  z = 3.36, p = 0.0008
  Statistically significant at alpha=0.05: True

Peeking simulation (control == treatment, i.e. null hypothesis true):
  False-positive rate if checking every 100 users and stopping early: 26.0%
  False-positive rate if analyzing once at a fixed sample size:       4.6%
```

The peeking result is itself a simulation, so the exact numbers vary run
to run — the qualitative point (peeking pushes the false-positive rate
well above 5%, a fixed-horizon look stays close to it) is stable.
