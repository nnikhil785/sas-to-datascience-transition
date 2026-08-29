# AI-Assisted SAS Macro Documenter

A real, working version of the "used Claude to accelerate documentation
for SAS macros" workflow referenced on the resume — parses a `.sas` file
and generates markdown documentation for every macro it finds.

## Two modes

- **Rule-based (default, no API key needed):** parses macro name,
  parameters, PROC steps, and referenced tables directly from the SAS
  source, and generates structured documentation from that — genuinely
  useful with zero API cost, and what's demonstrated by default in this
  repo.
- **AI mode (`--ai`):** if `ANTHROPIC_API_KEY` is set and `pip install
  anthropic` has been run, sends the same parsed structure to Claude to
  generate a sharper natural-language explanation and example usage on
  top of it. The AI narrates the parsed facts — it doesn't invent them.

## Running

```bash
pip install anthropic   # optional, only needed for --ai mode
python document_sas_macros.py ../../01-sas-to-python-r-migration/data_profiling_dictionary/sas/data_profiling_macro.sas
```

Add `--ai` (with `ANTHROPIC_API_KEY` set in your environment) for the
Claude-generated narrative version.

## Example output (rule-based mode)

```
## `%profile_dataset`

**Parameters:** `dsn`
**PROC steps used:** CONTENTS, MEANS, PRINT, SQL, TRANSPOSE
**Tables/datasets referenced:** work._contents, work._nmiss, work._nmiss_t, work.data_dictionary
**What it likely does:** Inspects dataset structure/metadata; computes summary
statistics (mean, min, max, missing counts); prints a dataset; queries or
joins data; reshapes data between wide and long formats.
```
