"""
A/B Test Analysis: Checkout Conversion

A complete experimentation workflow on a synthetic checkout-conversion
test (control vs. a new checkout flow) -- the kind of experiment behind
"optimizing checkout conversion" work in consumer-lending/fintech risk &
analytics teams. Covers the full lifecycle an experimentation-literate
analyst is expected to run:

  1. Pre-experiment power analysis (how many users do we need per arm?)
  2. Post-experiment hypothesis test (two-proportion z-test)
  3. Confidence interval on the lift
  4. A sanity check: a sequential/"peeking" simulation showing why
     stopping early on a significant-looking result inflates false
     positives -- the most common real-world experimentation mistake.

Run:
    python ab_test_analysis.py

Outputs (written next to this script):
    conversion_by_arm.png
    peeking_simulation.png
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import (confint_proportions_2indep,
                                           proportions_ztest,
                                           proportion_effectsize)

HERE = Path(__file__).resolve().parent
RNG = np.random.default_rng(1)


# --------------------------------------------------------------------------
# 1. Pre-experiment: how many users do we need per arm?
# --------------------------------------------------------------------------
def required_sample_size(baseline_rate: float, mde: float, alpha: float = 0.05,
                          power: float = 0.8) -> int:
    """
    mde = minimum detectable effect, expressed as an absolute lift
    (e.g. 0.02 = detect a 2-percentage-point lift over baseline).
    """
    effect_size = proportion_effectsize(baseline_rate, baseline_rate + mde)
    analysis = NormalIndPower()
    n = analysis.solve_power(effect_size=effect_size, alpha=alpha, power=power, ratio=1.0)
    return int(np.ceil(n))


# --------------------------------------------------------------------------
# 2. Simulate the experiment itself
# --------------------------------------------------------------------------
def simulate_experiment(n_per_arm: int, control_rate: float, treatment_rate: float):
    control_conversions = RNG.binomial(1, control_rate, n_per_arm)
    treatment_conversions = RNG.binomial(1, treatment_rate, n_per_arm)
    return control_conversions, treatment_conversions


def analyze_experiment(control: np.ndarray, treatment: np.ndarray, alpha: float = 0.05):
    count = np.array([treatment.sum(), control.sum()])
    nobs = np.array([len(treatment), len(control)])

    z_stat, p_value = proportions_ztest(count, nobs, alternative="two-sided")
    ci_low, ci_upp = confint_proportions_2indep(
        count[0], nobs[0], count[1], nobs[1], method="wald"
    )

    return {
        "control_rate": control.mean(),
        "treatment_rate": treatment.mean(),
        "lift_abs": treatment.mean() - control.mean(),
        "z_stat": z_stat,
        "p_value": p_value,
        "significant": p_value < alpha,
        "ci_low": ci_low,
        "ci_upp": ci_upp,
    }


# --------------------------------------------------------------------------
# 3. Peeking simulation: why stopping early inflates false positives
# --------------------------------------------------------------------------
def peeking_simulation(n_simulations: int = 2000, max_n_per_arm: int = 2000,
                        check_every: int = 100, true_rate: float = 0.10) -> tuple[float, float]:
    """
    Simulates experiments where control and treatment have the SAME true
    conversion rate (i.e. the null hypothesis is true), then checks how
    often a naive analyst would have stopped and declared "significant"
    at any interim look vs. only looking once at the end.
    """
    checkpoints = list(range(check_every, max_n_per_arm + 1, check_every))
    false_positive_if_peeking = 0
    false_positive_if_fixed_n = 0

    for _ in range(n_simulations):
        control = RNG.binomial(1, true_rate, max_n_per_arm)
        treatment = RNG.binomial(1, true_rate, max_n_per_arm)

        stopped_significant = False
        for n in checkpoints:
            count = np.array([treatment[:n].sum(), control[:n].sum()])
            nobs = np.array([n, n])
            _, p_value = proportions_ztest(count, nobs, alternative="two-sided")
            if p_value < 0.05:
                stopped_significant = True
                break
        if stopped_significant:
            false_positive_if_peeking += 1

        count_final = np.array([treatment.sum(), control.sum()])
        nobs_final = np.array([max_n_per_arm, max_n_per_arm])
        _, p_final = proportions_ztest(count_final, nobs_final, alternative="two-sided")
        if p_final < 0.05:
            false_positive_if_fixed_n += 1

    return (
        false_positive_if_peeking / n_simulations,
        false_positive_if_fixed_n / n_simulations,
    )


def main() -> None:
    # --- 1. Pre-experiment power analysis ---
    baseline_rate = 0.10
    mde = 0.02  # want to detect a 2pp lift (10% -> 12%)
    n_needed = required_sample_size(baseline_rate, mde)
    print(f"Pre-experiment power analysis:")
    print(f"  Baseline conversion: {baseline_rate:.0%}, MDE: +{mde:.0%} (absolute)")
    print(f"  Required sample size per arm (alpha=0.05, power=0.80): {n_needed:,}\n")

    # --- 2. Run + analyze the simulated experiment ---
    true_control_rate = 0.10
    true_treatment_rate = 0.12  # the real underlying lift we're trying to detect
    control, treatment = simulate_experiment(n_needed, true_control_rate, true_treatment_rate)
    results = analyze_experiment(control, treatment)

    print("Experiment results (single fixed-horizon analysis):")
    print(f"  Control conversion:   {results['control_rate']:.2%}  (n={len(control):,})")
    print(f"  Treatment conversion: {results['treatment_rate']:.2%}  (n={len(treatment):,})")
    print(f"  Absolute lift: {results['lift_abs']:+.2%}")
    print(f"  95% CI on lift: [{results['ci_low']:+.2%}, {results['ci_upp']:+.2%}]")
    print(f"  z = {results['z_stat']:.2f}, p = {results['p_value']:.4f}")
    print(f"  Statistically significant at alpha=0.05: {results['significant']}\n")

    # Bar chart of conversion by arm with 95% CIs
    fig, ax = plt.subplots(figsize=(5, 5))
    arms = ["Control", "Treatment"]
    rates = [results["control_rate"], results["treatment_rate"]]
    errors = [
        1.96 * np.sqrt(r * (1 - r) / n_needed) for r in rates
    ]
    ax.bar(arms, rates, yerr=errors, capsize=8, color=["#8899AA", "#1F3864"])
    ax.set_ylabel("Conversion Rate")
    ax.set_title("Checkout Conversion by Arm (95% CI)")
    for i, r in enumerate(rates):
        ax.text(i, r + errors[i] + 0.003, f"{r:.1%}", ha="center")
    fig.tight_layout()
    fig.savefig(HERE / "conversion_by_arm.png", dpi=150)
    plt.close(fig)

    # --- 3. Peeking simulation ---
    print("Peeking simulation (control == treatment, i.e. null hypothesis true):")
    peek_fpr, fixed_fpr = peeking_simulation(n_simulations=500)
    print(f"  False-positive rate if checking every 100 users and stopping early: {peek_fpr:.1%}")
    print(f"  False-positive rate if analyzing once at a fixed sample size:       {fixed_fpr:.1%}")
    print("  (Both 'should' be ~5% under a single valid test -- peeking inflates it well above that.)")

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(["Peek every 100 users\n(stop early if p<0.05)", "Fixed sample size\n(look once at the end)"],
           [peek_fpr, fixed_fpr], color=["#C0504D", "#1F3864"])
    ax.axhline(0.05, color="black", linestyle="--", linewidth=1, label="Nominal alpha = 0.05")
    ax.set_ylabel("False Positive Rate")
    ax.set_title("Why Peeking Inflates False Positives")
    ax.legend()
    fig.tight_layout()
    fig.savefig(HERE / "peeking_simulation.png", dpi=150)
    plt.close(fig)

    print(f"\nPlots written to {HERE}")


if __name__ == "__main__":
    main()
