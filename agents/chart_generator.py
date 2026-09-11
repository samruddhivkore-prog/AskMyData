"""
Agent 3 — Chart Generator

Looks at the shape of the query result (which columns are numbers vs
text/dates) and picks a sensible chart type — no LLM call needed here,
this one is plain logic, which keeps it fast and free to run.
"""
import pandas as pd
import plotly.express as px
from agents.state import AgentState


def generate_chart(state: AgentState) -> AgentState:
    rows = state.get("query_result") or []

    if not rows:
        return {**state, "chart_json": None}

    df = pd.DataFrame(rows)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    other_cols = [c for c in df.columns if c not in numeric_cols]

    if not numeric_cols or not other_cols:
        # Nothing sensible to plot (e.g. a single count) — skip the chart
        return {**state, "chart_json": None}

    x_col, y_col = other_cols[0], numeric_cols[0]

    if len(df) <= 15:
        fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
    else:
        fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} over {x_col}")

    return {**state, "chart_json": fig.to_json()}
