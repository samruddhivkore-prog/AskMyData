"""
Schema discovery — introspects the SQLite database directly instead of
hardcoding table/column names in a prompt string. This is the "explore
before query" step: the SQL Generator agent always sees the *actual*
current schema, so it can't hallucinate a column that doesn't exist, and
swapping in a different database doesn't require editing agent code.
"""
import sqlite3


def get_schema_description(db_path: str) -> str:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = [row[0] for row in cur.fetchall()]

    table_lines = ["Tables:"]
    fk_lines = []
    for table in tables:
        cur.execute(f"PRAGMA table_info({table})")
        columns = cur.fetchall()  # cid, name, type, notnull, dflt_value, pk
        col_desc = ", ".join(f"{c[1]} {c[2]}" for c in columns)
        table_lines.append(f"- {table}({col_desc})")

        cur.execute(f"PRAGMA foreign_key_list({table})")
        for fk in cur.fetchall():
            # id, seq, table, from, to, on_update, on_delete, match
            fk_lines.append(f"  {table}.{fk[3]} -> {fk[2]}.{fk[4]}")

    conn.close()

    schema = "\n".join(table_lines)
    if fk_lines:
        schema += "\n\nForeign keys:\n" + "\n".join(fk_lines)
    return schema
