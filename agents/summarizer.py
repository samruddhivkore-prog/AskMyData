"""
Agent 4 — Summarizer

Takes the raw query results and writes a short, plain-English answer,
so the person asking doesn't have to read a results table themselves.
"""
from langchain_core.prompts import ChatPromptTemplate
from agents.state import AgentState
from agents.llm import get_llm

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You answer business questions in 1-3 plain-English sentences "
            "based on SQL query results. Be concise and specific — use "
            "actual numbers from the data. No preamble.",
        ),
        ("human", "Question: {question}\n\nResults: {results}"),
    ]
)


def summarize(state: AgentState) -> AgentState:
    results = state.get("query_result")

    if not results:
        return {**state, "summary": "No matching data was found for that question."}

    llm = get_llm()
    chain = PROMPT | llm
    response = chain.invoke({"question": state["question"], "results": results})

    return {**state, "summary": response.content.strip()}
