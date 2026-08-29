"""
AI-Assisted SAS Macro Documenter

Reads a .sas file, parses out its macro(s), PROC steps, and parameters,
and produces markdown documentation. This is a real, working version of
the "used Claude to accelerate documentation generation for SAS macros"
workflow referenced on the resume.

Two modes:
  1. AI mode (if ANTHROPIC_API_KEY is set and the `anthropic` package is
     installed): sends the parsed macro structure to Claude to generate a
     natural-language explanation of what the macro does and how to use it.
  2. Rule-based fallback mode (default, no API key required): parses the
     macro structurally (name, parameters, PROC steps used, table
     references) and generates structured markdown documentation directly.
     This mode always runs and is what's demonstrated in this repo by
     default -- so the tool is genuinely useful even with zero API cost,
     and the AI mode is a strict upgrade on top of it.

Usage:
    python document_sas_macros.py path/to/file.sas
    python document_sas_macros.py path/to/file.sas --out docs.md
"""
from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MacroInfo:
    name: str
    params: list[str]
    proc_steps: list[str] = field(default_factory=list)
    tables_referenced: set[str] = field(default_factory=set)
    body: str = ""


def parse_sas_macros(sas_text: str) -> list[MacroInfo]:
    """Extracts %macro ... %mend blocks and structural details from SAS source."""
    macros = []
    pattern = re.compile(
        r"%macro\s+(\w+)\s*(?:\(([^)]*)\))?\s*;(.*?)%mend", re.IGNORECASE | re.DOTALL
    )
    for match in pattern.finditer(sas_text):
        name = match.group(1)
        raw_params = match.group(2) or ""
        params = [p.strip() for p in raw_params.split(",") if p.strip()]
        body = match.group(3)

        raw_steps = re.findall(r"proc\s+(\w+)", body, re.IGNORECASE)
        proc_steps = sorted({s.upper() for s in raw_steps})
        tables = set(re.findall(r"\b(?:data|from|join)\b\s*=?\s*([\w.]+)", body, re.IGNORECASE))
        tables = {t for t in tables if not t.startswith("_") and len(t) > 2}

        macros.append(MacroInfo(
            name=name, params=params, proc_steps=proc_steps,
            tables_referenced=tables, body=body.strip()
        ))
    return macros


def render_fallback_doc(macro: MacroInfo, source_file: str) -> str:
    """Rule-based structured documentation -- no AI required."""
    lines = [
        f"## `%{macro.name}`",
        "",
        f"*Parsed from `{source_file}`*",
        "",
        "**Parameters:** " + (", ".join(f"`{p}`" for p in macro.params) if macro.params else "_none_"),
        "",
        "**PROC steps used:** " + (", ".join(macro.proc_steps) if macro.proc_steps else "_none detected_"),
        "",
        "**Tables/datasets referenced:** "
        + (", ".join(sorted(macro.tables_referenced)) if macro.tables_referenced else "_none detected_"),
        "",
        "**What it likely does:** "
        + summarize_by_proc_steps(macro.proc_steps),
        "",
    ]
    return "\n".join(lines)


def summarize_by_proc_steps(proc_steps: list[str]) -> str:
    """A small rules table mapping common PROC steps to plain-English purpose --
    the deterministic 'v1' of what an LLM call would otherwise generate."""
    step_meanings = {
        "sql": "queries or joins data",
        "freq": "produces frequency/crosstab summaries",
        "means": "computes summary statistics (mean, min, max, missing counts)",
        "contents": "inspects dataset structure/metadata",
        "transpose": "reshapes data between wide and long formats",
        "report": "produces a formatted tabular report",
        "print": "prints a dataset",
        "sort": "sorts a dataset",
    }
    known = [step_meanings[s.lower()] for s in proc_steps if s.lower() in step_meanings]
    if not known:
        return "performs custom data-step logic (no recognized PROC steps found)."
    return "; ".join(known).capitalize() + "."


def render_ai_doc(macro: MacroInfo, source_file: str) -> str:
    """AI mode: ask Claude to write the narrative explanation. Requires the
    `anthropic` package and ANTHROPIC_API_KEY to be set."""
    import anthropic  # local import: optional dependency

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment
    prompt = f"""You are documenting a SAS macro for a data engineering handoff.

Macro name: %{macro.name}
Parameters: {', '.join(macro.params) or 'none'}
PROC steps used: {', '.join(macro.proc_steps) or 'none'}
Tables referenced: {', '.join(sorted(macro.tables_referenced)) or 'none'}

Macro body:
```sas
{macro.body}
```

Write a concise markdown section (## heading with the macro name) explaining:
1. What the macro does, in plain English
2. What each parameter controls
3. An example call
Keep it under 200 words."""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def document_file(path: Path, use_ai: bool) -> str:
    sas_text = path.read_text()
    macros = parse_sas_macros(sas_text)

    if not macros:
        return f"# {path.name}\n\nNo `%macro ... %mend` blocks found in this file.\n"

    sections = [f"# Documentation: `{path.name}`", ""]
    for macro in macros:
        if use_ai:
            try:
                sections.append(render_ai_doc(macro, path.name))
                continue
            except Exception as exc:  # noqa: BLE001 -- fall back cleanly on any AI-path error
                sections.append(f"_(AI documentation failed: {exc}; falling back to rule-based mode)_\n")
        sections.append(render_fallback_doc(macro, path.name))

    return "\n".join(sections)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate documentation for SAS macros.")
    parser.add_argument("sas_file", type=Path, help="Path to a .sas file")
    parser.add_argument("--out", type=Path, default=None, help="Output markdown path")
    parser.add_argument(
        "--ai", action="store_true",
        help="Use Claude (requires `pip install anthropic` and ANTHROPIC_API_KEY)",
    )
    args = parser.parse_args()

    use_ai = args.ai and bool(os.environ.get("ANTHROPIC_API_KEY"))
    if args.ai and not use_ai:
        print("Warning: --ai requested but ANTHROPIC_API_KEY is not set; using rule-based mode.")

    doc = document_file(args.sas_file, use_ai=use_ai)

    if args.out:
        args.out.write_text(doc)
        print(f"Documentation written to {args.out}")
    else:
        print(doc)


if __name__ == "__main__":
    main()
