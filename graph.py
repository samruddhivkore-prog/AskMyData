"""
This is the "crew" — it wires the four agents into a graph and defines
the order they run in, including the retry loop between SQL generation
and execution.

Flow:
    generate_sql -> execute_sql --(error, retries left)--> generate_sql
                                --(error, no retries left)--> END
                                --(success)--> generate_chart -> summarize -> END
"""
from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.sql_generator import generate_sql
from agents.sql_executor import execute_sql, should_retry
from agents.chart_generator import generate_chart
from agents.summarizer import summarize


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("generate_sql", generate_sql)
    graph.add_node("execute_sql", execute_sql)
    graph.add_node("generate_chart", generate_chart)
    graph.add_node("summarize", summarize)

    graph.set_entry_point("generate_sql")
    graph.add_edge("generate_sql", "execute_sql")

    graph.add_conditional_edges(
        "execute_sql",
        should_retry,
        {
            "retry": "generate_sql",
            "give_up": END,
            "continue": "generate_chart",
        },
    )

    graph.add_edge("generate_chart", "summarize")
    graph.add_edge("summarize", END)

    return graph.compile()


def run_pipeline(question: str) -> dict:
    """Convenience wrapper used by the Streamlit app."""
    app = build_graph()
    initial_state: AgentState = {
        "question": question,
        "sql_query": None,
        "query_result": None,
        "error": None,
        "retry_count": 0,
        "chart_json": None,
        "summary": None,
    }
    return app.invoke(initial_state)