# AI-Agentic Workflows

Working examples of AI-assisted analytics automation — the "building
projects/workflows and migrating SAS work using Claude" story referenced
on the resume, made concrete rather than left as a bullet point.

| Project | What it does |
|---|---|
| [`sas_macro_documenter/`](sas_macro_documenter/) | Parses a `.sas` file and generates markdown documentation for its macros — rule-based by default, upgradeable to Claude-generated narrative |
| [`data_quality_agent/`](data_quality_agent/) | Automates DAQC-style data quality review: rule-based scorecard + optional Claude-generated stakeholder narrative |

Both tools are designed so the **AI is additive, not load-bearing**: each
runs correctly and produces real, useful output with zero API cost via a
deterministic rule-based mode, and `--ai` (with `ANTHROPIC_API_KEY` set)
is a strict upgrade that narrates the same underlying facts rather than
replacing them — a deliberate pattern for building AI features that
degrade gracefully instead of failing outright when a key isn't present.
