"""
Single place that decides which LLM backend the agents talk to, so
switching between a paid API and a free local model is a one-line change
in .env rather than an edit to every agent file.

    LLM_PROVIDER=openai   (default) -> OpenAI API, needs OPENAI_API_KEY
    LLM_PROVIDER=ollama             -> local model via Ollama, no API key

LLM_MODEL overrides the model name for either provider (defaults below).
"""
import os


def get_llm(temperature: float = 0):
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        model = os.getenv("LLM_MODEL", "llama3.2:3b")
        return ChatOllama(model=model, temperature=temperature)

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=model, temperature=temperature)

    raise ValueError(
        f"Unknown LLM_PROVIDER '{provider}' — use 'openai' or 'ollama'."
    )
