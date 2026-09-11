"""
Agent 2 — SQL Executor & Verifier

Runs the generated query against the real SQLite database. This is the
"guardrail" agent: it blocks anything that isn't a single read-only
SELECT (no DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE — ever,
no matter what the LLM wrote), and if the query errors out, it records
the error so Agent 1 can retry with that context. This retry loop is
what the graph uses to "self-correct".

When a retry *succeeds*, this agent also logs the (failed_sql, error,
fixed_sql) triple to the meta-error memory, so a similar mistake on a
future question can be avoided on the first attempt instead of needing
its own retry.
"""
import os
import re
import sqlite3
from agents.state import AgentState
from agents.error_memory import record_fix

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "company.db")
MAX_RETRIES = 2

FORBIDDEN_KEYWORDS = [
    "drop", "delete", "update", "insert", "alter",
    "create", "truncate", "replace", "attach", "pragma",
]


def _is_safe_select(sql: str) -> bool:
    normalized = sql.strip().lower()
    if not normalized.startswith("select"):
        return False

    # Reject stacked statements — only a single trailing semicolon (or
    # none) is allowed, never a semicolon followed by more SQL.
    body = normalized[:-1] if normalized.endswith(";") else normalized
    if ";" in body:
        return False

    # Match whole words only, so e.g. a column named "updated_at" doesn't
    # trip the "update" guardrail.
    tokens = set(re.findall(r"[a-z_]+", body))
    return not (tokens & set(FORBIDDEN_KEYWORDS))


def execute_sql(state: AgentState) -> AgentState:
    sql = state.get("sql_query", "")

    if not _is_safe_select(sql):
        return {
            **state,
            "error": "Query blocked: only a single read-only SELECT statement is allowed.",
            "retry_count": state.get("retry_count", 0) + 1,
        }

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql)
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()

        # This attempt succeeded — if it followed a failed one, log the fix.
        if state.get("last_failed_sql"):
            record_fix(
                question=state["question"],
                failed_sql=state["last_failed_sql"],
                error=state.get("last_failed_error", ""),
                fixed_sql=sql,
            )

        return {
            **state,
            "query_result": rows,
            "error": None,
            "last_failed_sql": None,
            "last_failed_error": None,
        }

    except sqlite3.Error as e:
        return {
            **state,
            "error": str(e),
            "retry_count": state.get("retry_count", 0) + 1,
        }


def should_retry(state: AgentState) -> str:
    """Conditional edge: decides where the graph goes next."""
    if state.get("error") and state.get("retry_count", 0) <= MAX_RETRIES:
        return "retry"
    if state.get("error"):
        return "give_up"
    return "continue"
