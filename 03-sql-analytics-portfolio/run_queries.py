"""
Executes every query in analytical_queries.sql against portfolio.db and
prints the results -- proof that each query actually runs correctly
against real (if synthetic) data.

Run:
    python setup_sqlite_db.py   # first, to build portfolio.db
    python run_queries.py
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent


def split_queries(sql_text: str) -> list[tuple[str, str]]:
    """Splits the .sql file into (comment_title, query) pairs, one per
    '-- Query N:' marker through to the next marker (or end of file)."""
    markers = list(re.finditer(r"-- (Query \d+:.*)", sql_text))
    queries = []
    for i, m in enumerate(markers):
        title = m.group(1).strip()
        start = m.end()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(sql_text)
        chunk = sql_text[start:end]
        body_lines = [ln for ln in chunk.splitlines() if not ln.strip().startswith("--")]
        body = "\n".join(body_lines).strip()
        if body:
            queries.append((title, body))
    return queries


def main() -> None:
    db_path = HERE / "portfolio.db"
    if not db_path.exists():
        raise SystemExit("portfolio.db not found -- run setup_sqlite_db.py first.")

    conn = sqlite3.connect(db_path)
    sql_text = (HERE / "analytical_queries.sql").read_text()
    queries = split_queries(sql_text)

    for title, query in queries:
        print("=" * 70)
        print(title)
        print("=" * 70)
        df = pd.read_sql_query(query, conn)
        print(df.head(15).to_string(index=False))
        print(f"({len(df)} total rows)\n")

    conn.close()


if __name__ == "__main__":
    main()
