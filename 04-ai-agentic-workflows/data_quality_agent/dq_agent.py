"""
Data Quality Agent

Automates the kind of Data Analytics Quality Control (DAQC) review
described on the resume: checking a dataset against a set of rules
(missingness thresholds, uniqueness, allowed ranges/categories) and
producing a pass/fail scorecard plus a plain-English narrative summary.

Two modes:
  1. Rule-based mode (default, always runs): applies configurable checks
     and produces a structured scorecard + a templated narrative.
  2. AI narrative mode (--ai, requires ANTHROPIC_API_KEY): sends the
     rule-based scorecard to Claude to write a sharper, more nuanced
     stakeholder-ready narrative on top of the same deterministic checks
     -- the AI never invents the checks or the numbers, only narrates them.

Usage:
    python dq_agent.py path/to/data.csv --rules rules.json
    python dq_agent.py path/to/data.csv --rules rules.json --ai
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class CheckResult:
    check_name: str
    column: str
    passed: bool
    detail: str


DEFAULT_RULES = {
    "max_missing_pct": 5.0,
    "required_columns": [],
    "unique_columns": [],
    "range_checks": {},      # {"column": [min, max]}
    "allowed_values": {},    # {"column": ["A", "B", "C"]}
}


def load_rules(path: Path | None) -> dict:
    if path is None:
        return DEFAULT_RULES
    user_rules = json.loads(path.read_text())
    merged = dict(DEFAULT_RULES)
    merged.update(user_rules)
    return merged


def run_checks(df: pd.DataFrame, rules: dict) -> list[CheckResult]:
    results = []
    n = len(df)

    for col in rules["required_columns"]:
        results.append(CheckResult(
            "required_column_present", col, col in df.columns,
            "present" if col in df.columns else "MISSING FROM DATASET",
        ))

    for col in df.columns:
        pct_missing = df[col].isna().mean() * 100
        passed = pct_missing <= rules["max_missing_pct"]
        results.append(CheckResult(
            "missingness_threshold", col, passed,
            f"{pct_missing:.1f}% missing (threshold {rules['max_missing_pct']}%)",
        ))

    for col in rules["unique_columns"]:
        if col not in df.columns:
            continue
        n_dupes = int(df[col].duplicated().sum())
        results.append(CheckResult(
            "uniqueness", col, n_dupes == 0,
            f"{n_dupes} duplicate value(s)" if n_dupes else "all values unique",
        ))

    for col, (lo, hi) in rules["range_checks"].items():
        if col not in df.columns:
            continue
        out_of_range = int(((df[col] < lo) | (df[col] > hi)).sum())
        results.append(CheckResult(
            "range_check", col, out_of_range == 0,
            f"{out_of_range} value(s) outside [{lo}, {hi}]" if out_of_range else f"all values within [{lo}, {hi}]",
        ))

    for col, allowed in rules["allowed_values"].items():
        if col not in df.columns:
            continue
        bad_values = df.loc[~df[col].isin(allowed), col].unique().tolist()
        results.append(CheckResult(
            "allowed_values", col, len(bad_values) == 0,
            f"unexpected values: {bad_values}" if bad_values else "all values within allowed set",
        ))

    return results


def render_scorecard(results: list[CheckResult]) -> pd.DataFrame:
    df = pd.DataFrame([r.__dict__ for r in results])
    df["status"] = df["passed"].map({True: "PASS", False: "FAIL"})
    return df[["check_name", "column", "status", "detail"]]


def render_fallback_narrative(results: list[CheckResult], n_rows: int, n_cols: int) -> str:
    n_pass = sum(r.passed for r in results)
    n_fail = len(results) - n_pass
    failures = [r for r in results if not r.passed]

    lines = [
        f"Data Quality Review — {n_rows:,} rows x {n_cols} columns",
        f"{n_pass}/{len(results)} checks passed.",
        "",
    ]
    if failures:
        lines.append("Issues found:")
        for f in failures:
            lines.append(f"  - [{f.check_name}] {f.column}: {f.detail}")
    else:
        lines.append("No data quality issues found against the configured rules.")
    return "\n".join(lines)


def render_ai_narrative(results: list[CheckResult], n_rows: int, n_cols: int) -> str:
    import anthropic  # local import: optional dependency

    scorecard_text = "\n".join(
        f"- [{r.check_name}] {r.column}: {'PASS' if r.passed else 'FAIL'} -- {r.detail}"
        for r in results
    )
    prompt = f"""You are a data quality analyst summarizing an automated DAQC-style review
for a business stakeholder who is not technical.

Dataset: {n_rows:,} rows, {n_cols} columns.

Rule-based check results (these are the ONLY facts you may use -- do not
invent additional issues or numbers):
{scorecard_text}

Write a concise (under 150 words) stakeholder-ready summary: overall
health, the most important issues to act on first, and one clear
recommendation."""

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def main() -> None:
    parser = argparse.ArgumentParser(description="Automated data quality review agent.")
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--rules", type=Path, default=None, help="Path to a rules JSON file")
    parser.add_argument("--ai", action="store_true", help="Use Claude for the narrative summary")
    args = parser.parse_args()

    df = pd.read_csv(args.csv_file)
    rules = load_rules(args.rules)
    results = run_checks(df, rules)
    scorecard = render_scorecard(results)

    print(scorecard.to_string(index=False))
    print()

    use_ai = args.ai and bool(os.environ.get("ANTHROPIC_API_KEY"))
    if args.ai and not use_ai:
        print("Warning: --ai requested but ANTHROPIC_API_KEY is not set; using fallback narrative.\n")

    if use_ai:
        try:
            print(render_ai_narrative(results, len(df), len(df.columns)))
            return
        except Exception as exc:  # noqa: BLE001
            print(f"(AI narrative failed: {exc}; falling back to rule-based narrative)\n")

    print(render_fallback_narrative(results, len(df), len(df.columns)))


if __name__ == "__main__":
    main()
