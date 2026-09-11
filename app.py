"""
Run with:  streamlit run app.py

A minimal front end for the multi-agent pipeline: type a plain-English
question about the sample sales data, and watch the SQL, results, and
chart come back.
"""
import os
import streamlit as st
import pandas as pd
import plotly.io as pio
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Multi-Agent SQL Analyst", layout="wide")
st.title(" Multi-Agent SQL & Data Analyst")
st.caption(
    "Ask a plain-English question. A SQL agent writes the query, an "
    "execution agent runs and verifies it (retrying on error), and a "
    "chart agent visualizes the result."
)

llm_provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
if llm_provider == "openai" and not os.getenv("OPENAI_API_KEY"):
    st.warning(
        "No OPENAI_API_KEY found. Copy .env.example to .env and add your "
        "key before running a query — or set LLM_PROVIDER=ollama in .env "
        "to use a free local model instead."
    )
elif llm_provider == "ollama":
    st.caption("Using local model via Ollama (LLM_PROVIDER=ollama) — no API key needed.")

question = st.text_input(
    "Your question",
    placeholder="e.g. What were total sales by product category?",
)

if st.button("Run", type="primary") and question:
    with st.spinner("Agents working..."):
        from graph import run_pipeline  # imported here so the page loads even without an API key

        result = run_pipeline(question)

    if result.get("error"):
        st.error(f"Couldn't get a working query after retries: {result['error']}")
    else:
        st.subheader("Answer")
        st.write(result.get("summary", ""))

        with st.expander("Generated SQL"):
            st.code(result.get("sql_query", ""), language="sql")

        rows = result.get("query_result") or []
        if rows:
            st.subheader("Data")
            st.dataframe(pd.DataFrame(rows))

        if result.get("chart_json"):
            st.subheader("Chart")
            fig = pio.from_json(result["chart_json"])
            st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption(
    "Sample data covers customers, products, and orders from May–Aug 2026. "
    "Try: 'top 3 products by revenue', 'total orders per country', "
    "'sales by product category'."
)
