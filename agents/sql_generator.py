"""
Agent 1 — SQL Generator

Turns a plain-English question into a SQL SELECT query. Before writing
anything it gets two kinds of grounding context: the database's actual
schema (introspected live, not hardcoded — see database/schema.py) and,
if a similar question has caused a mistake before, the fix that worked
last time (see agents/error_memory.py). If the previous attempt in this
run failed (state["error"] is set), it also gets that error so it can
fix its own mistake — this is what makes the pipeline "self-correcting"
rather than a single fire-and-forget script.
"""
import os
from langchain_core.prompts import ChatPromptTemplate
from agents.state import AgentState
from agents.llm import get_llm
from agents.error_memory import relevant_fixes, format_fixes_for_prompt
from database.schema import get_schema_description

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "company.db")

# Domain knowledge that isn't derivable from column names alone — kept
# separate from the schema itself so schema stays auto-discovered.
DOMAIN_NOTES = """
Notes:
- Revenue for a line item = order_items.quantity * products.price
- Join order_items -> products on product_id, order_items -> orders on order_id
"""

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a careful SQLite expert. Given a database schema and a "
            "question, write ONE syntactically correct SQLite SELECT query "
            "that answers it. Only output the raw SQL — no explanation, no "
            "markdown code fences, no semicolon-separated multiple statements. "
            "Never write INSERT, UPDATE, DELETE, or DROP statements.",
        ),
        (
            "human",
            "Schema:\n{schema}\n\n"
            "{domain_notes}\n\n"
            "{known_fixes}\n\n"
            "Question: {question}\n\n"
            "{error_context}",
        ),
    ]
)


def generate_sql(state: AgentState) -> AgentState:
    llm = get_llm()

    updates = {}
    error_context = ""
    if state.get("error"):
        error_context = (
            f"Your previous query failed with this error:\n{state['error']}\n"
            f"Previous query was: {state.get('sql_query')}\n"
            "Please fix the query."
        )
        # Remember what failed so that, if this retry succeeds, execute_sql
        # can log the (failed_sql, error, fixed_sql) triple to memory.
        updates["last_failed_sql"] = state.get("sql_query")
        updates["last_failed_error"] = state["error"]

    fixes = relevant_fixes(state["question"])
    known_fixes = format_fixes_for_prompt(fixes)

    chain = PROMPT | llm
    response = chain.invoke(
        {
            "schema": get_schema_description(DB_PATH),
            "domain_notes": DOMAIN_NOTES,
            "known_fixes": known_fixes,
            "question": state["question"],
            "error_context": error_context,
        }
    )

    sql = response.content.strip()
    # Strip markdown fences if the model adds them anyway
    sql = sql.replace("```sql", "").replace("```", "").strip()

    return {**state, **updates, "sql_query": sql, "error": None}
