# Multi-Agent SQL & Data Analyst

Ask a plain-English business question, get a SQL query, a verified
result, and a chart — built as four small agents coordinated by
LangGraph instead of one big script.

## Architecture

```
                ┌───────────────┐
   question --> │ generate_sql  │  (Agent 1: NL -> SQL)
                └───────┬───────┘
                        ▼
                ┌───────────────┐   error, retries left
                │  execute_sql  │ ─────────────────────┐
                └───────┬───────┘                       │
                  success│  error, out of retries        │
                        ▼        │                       │
                ┌───────────────┐▼                       │
                │ generate_chart│ (END, reports failure)  │
                └───────┬───────┘                         │
                        ▼                                 │
                ┌───────────────┐                          │
                │   summarize   │                          │
                └───────┬───────┘                          │
                        ▼                                  │
                       END  <───────────────────────────────┘
```

- **`generate_sql`** — writes a SQLite `SELECT` from the question, the
  database's live schema (introspected on every call, see
  `database/schema.py` — never hardcoded, so it can't hallucinate a
  column that doesn't exist), and, on retry, the previous error.
- **`execute_sql`** — the guardrail: rejects anything that isn't a single
  read-only `SELECT` (whole-word block on DROP/DELETE/UPDATE/INSERT/
  ALTER/CREATE/TRUNCATE/etc., and no stacked statements), runs it, and
  reports back success or an error.
- **`generate_chart`** — no LLM needed here; picks bar vs. line based on
  the shape of the result and builds a Plotly figure.
- **`summarize`** — writes a short plain-English answer from the data.

The retry loop between `generate_sql` and `execute_sql` is the "self
-correcting" part — if the SQL fails, the error goes back to Agent 1
with context, up to 2 retries, before the pipeline gives up cleanly.

**Meta-error memory** (`agents/error_memory.py`): whenever a retry
succeeds, the (wrong SQL, error, fixed SQL) triple is logged to
`database/error_memory.json`. On every new question, the most similar
past fixes are pulled back into Agent 1's prompt — so a mistake made on
one question doesn't get repeated on a *different* but similar question
in a later run, without needing its own retry first.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then paste your OpenAI key into .env

python database/init_db.py      # creates the sample SQLite database
streamlit run app.py
```

Try questions like:
- "What were total sales by product category?"
- "Which 3 customers spent the most?"
- "How many orders came from Ireland?"

## Using a free local model instead of OpenAI

Both LLM-calling agents (`sql_generator.py`, `summarizer.py`) get their
model from `agents/llm.py`, which picks the backend based on `.env` — no
code changes needed:

1. Install [Ollama](https://ollama.com) and run `ollama pull llama3.2:3b`
   (don't just run bare `ollama` — its interactive picker defaults to
   showing cloud-hosted models, which need sign-in/billing and aren't
   what you want here)
2. Make sure the Ollama app/service is running
3. In `.env`, set:
   ```
   LLM_PROVIDER=ollama
   ```
   (`OPENAI_API_KEY` isn't needed in this mode.)

To go back to OpenAI, set `LLM_PROVIDER=openai` (or remove the line — it's
the default) and make sure `OPENAI_API_KEY` is set. `LLM_MODEL` overrides
the model name for either provider if you want something other than
`gpt-4o-mini` / `llama3.2:3b`.

Heads up on accuracy: smaller local models are noticeably worse at
text-to-SQL than GPT-4o-mini-class models on anything beyond simple
single-table queries — expect more retries (and occasional give-ups) on
multi-join or aggregation-heavy questions with `llama3.2:3b` than with
OpenAI. If it's struggling, `ollama pull llama3.1:8b` and set
`LLM_MODEL=llama3.1:8b` for a stronger (larger, slower) local option.

## Next steps to make this a strong portfolio piece

1. **Deploy it** — [Streamlit Community Cloud](https://streamlit.io/cloud)
   or [Hugging Face Spaces](https://huggingface.co/spaces) both have free
   tiers; either turns this into a link a recruiter can actually click.
2. **Push to GitHub** — `git init`, commit, and write a good top-level
   README (this one's a start) with a screenshot or short GIF of it running.
3. **Extend it** — swap the sample database for something you know well
   (e.g. your O-RAN dataset), or add a 5th agent that catches ambiguous
   questions and asks a clarifying one before generating SQL.
4. **Add a couple of automated tests** for `sql_executor.py`'s guardrail
   (confirm it actually blocks `DROP TABLE` etc.) — a small `tests/`
   folder with 3-4 test cases signals production thinking, not just a demo.
