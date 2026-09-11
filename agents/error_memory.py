"""
Meta-error memory — a small persistent log of past (question, wrong SQL,
error, fixed SQL) records. When a retry succeeds, the fix gets logged
here; on future questions, the most similar past fixes are pulled back
into the SQL Generator's prompt as extra context.

This is separate from the in-run retry loop: the retry loop fixes the
*current* query using the error it just saw, while this memory helps the
*first* attempt on a new-but-similar question avoid a mistake made
before, across separate runs of the app.
"""
import json
import os
from typing import Any, Dict, List

STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "error_memory.json")
MAX_ENTRIES = 200


def _load() -> List[Dict[str, Any]]:
    if not os.path.exists(STORE_PATH):
        return []
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(entries: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(entries[-MAX_ENTRIES:], f, indent=2)


def record_fix(question: str, failed_sql: str, error: str, fixed_sql: str) -> None:
    entries = _load()
    entries.append(
        {
            "question": question,
            "failed_sql": failed_sql,
            "error": error,
            "fixed_sql": fixed_sql,
        }
    )
    _save(entries)


def relevant_fixes(question: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Rank past fixes by word overlap with the current question. No
    embeddings needed at the scale a demo app's memory file will reach."""
    entries = _load()
    if not entries:
        return []

    q_words = set(question.lower().split())

    def overlap(entry: Dict[str, Any]) -> int:
        return len(q_words & set(entry["question"].lower().split()))

    ranked = sorted(entries, key=overlap, reverse=True)
    return [e for e in ranked if overlap(e) > 0][:limit]


def format_fixes_for_prompt(fixes: List[Dict[str, Any]]) -> str:
    if not fixes:
        return ""
    lines = ["Known fixes for similar past mistakes:"]
    for f in fixes:
        lines.append(
            f'- Question: "{f["question"]}"\n'
            f"  Wrong SQL: {f['failed_sql']}\n"
            f"  Error: {f['error']}\n"
            f"  Fixed SQL: {f['fixed_sql']}"
        )
    return "\n".join(lines)
