# AskMyData

**Ask a plain-English business question. Get back a SQL query, a verified
result, a chart, and a written answer.**

AskMyData is a small multi-agent data analyst built with
[LangGraph](https://github.com/langchain-ai/langgraph): four single-purpose
agents — write SQL, run &amp; verify it, chart it, summarize it — coordinated
as a graph instead of one large prompt. A failed query loops back and
retries with the error attached, and a fix that worked once is remembered
so the same mistake isn't repeated on a different question later.

🔗 **Live demo:** _add your Streamlit Community Cloud URL here after deploying (see below)_

```
Q: "top 3 products by revenue"

  → SELECT p.name, SUM(oi.quantity * p.price) AS revenue
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.name ORDER BY revenue DESC LIMIT 3;

  → Mechanical Keyboard   $239.96
    Wireless Mouse         $99.95
    Webcam HD               $90.00

  → "The top 3 products by revenue are the Mechanical Keyboard ($239.96),
     Wireless Mouse ($99.95), and Webcam HD ($90.00)."
```

## Features

- **Plain-English → SQL** — no query language to learn; the schema is
  introspected live from SQLite, never hardcoded, so it can't hallucinate a
  column that doesn't exist.
- **Self-correcting** — a failed query's error is fed back to the SQL
  writer, up to 2 retries, before the pipeline gives up cleanly.
- **Cross-run memory** — once a retry fixes a mistake, that (question,
  error, fix) is logged and resurfaced on future similar questions, so the
  *first* attempt avoids it instead of needing its own retry.
- **Guardrailed execution** — only a single read-only `SELECT` is ever run;
  `DROP`/`DELETE`/`UPDATE`/`INSERT`/`ALTER`/etc. and stacked statements are
  rejected before they reach the database.
- **Auto-charted results** — bar or line, picked from the shape of the
  result, no chart config needed.
- **Two interchangeable LLM backends** — OpenAI (`gpt-4o-mini`) for
  accuracy, or a free local model via Ollama (`llama3.2:3b`) — one line in
  `.env`, no code changes.

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

| Agent | File | Calls an LLM? | Job |
|---|---|---|---|
| 1. `generate_sql` | `agents/sql_generator.py` | Yes | Writes one SQLite `SELECT` from the question, the live schema, domain notes, and (on retry) the previous error + similar past fixes |
| 2. `execute_sql` | `agents/sql_executor.py` | No | Blocks anything but a single read-only `SELECT`, runs it, reports success/error, logs fixes to memory |
| 3. `generate_chart` | `agents/chart_generator.py` | No | Picks bar vs. line from the result's shape and builds a Plotly figure |
| 4. `summarize` | `agents/summarizer.py` | Yes | Writes a 1–3 sentence plain-English answer from the data |

**Meta-error memory** (`agents/error_memory.py`): whenever a retry
succeeds, the (wrong SQL, error, fixed SQL) triple is logged to
`database/error_memory.json`. On every new question, the most similar past
fixes are pulled back into Agent 1's prompt — so a mistake made on one
question doesn't get repeated on a *different* but similar question in a
later run, without needing its own retry first.

Full write-up (including a diagram of the retry/memory loops and a
quantitative breakdown of the codebase) is in
[`PROJECT_REPORT.txt`](PROJECT_REPORT.txt).

## Tech stack

`langgraph` · `langchain` (+ `langchain-openai` / `langchain-ollama`) ·
`streamlit` · `sqlite3` · `pandas` · `plotly`

## Getting started

```bash
git clone https://github.com/samruddhivkore-prog/AskMyData.git
cd AskMyData

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then paste your OpenAI key into .env
streamlit run app.py            # sample database is created automatically on first run
```

Try questions like:
- "What were total sales by product category?"
- "Which 3 customers spent the most?"
- "How many orders came from Ireland?"

### Using a free local model instead of OpenAI

Both LLM-calling agents (`sql_generator.py`, `summarizer.py`) get their
model from `agents/llm.py`, which picks the backend based on `.env` — no
code changes needed:

1. Install [Ollama](https://ollama.com) and run `ollama pull llama3.2:3b`
   (don't just run bare `ollama` — its interactive picker defaults to
   showing cloud-hosted models, which need sign-in/billing and aren't what
   you want here)
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

## Deploying

The app is ready to deploy as-is to **[Streamlit Community
Cloud](https://share.streamlit.io)** (free):

1. Push this repo to GitHub (already done if you're reading this there).
2. Go to [share.streamlit.io](https://share.streamlit.io) → sign in with
   GitHub → **New app**.
3. Pick this repo, branch `main`, main file path `app.py`.
4. Under **Advanced settings → Secrets**, paste:
   ```toml
   LLM_PROVIDER = "openai"
   OPENAI_API_KEY = "sk-..."
   ```
   (Ollama can't run on a free cloud host — it needs a local model server —
   so the deployed app always uses OpenAI regardless of what `.env` says
   locally. `app.py` bridges these secrets into the environment
   automatically, the same way `.env` works locally.)
5. **Deploy.** The sample SQLite database is generated automatically on
   first run (see `app.py`), so no build step is needed.

Paste the resulting `*.streamlit.app` URL into the **Live demo** line at
the top of this README.

## Project structure

```
AskMyData/
├── app.py                    Streamlit front end
├── graph.py                  builds & runs the LangGraph pipeline
├── requirements.txt
├── PROJECT_REPORT.txt        detailed write-up: architecture, quantitative stats, roadmap
├── agents/
│   ├── state.py               shared AgentState schema
│   ├── llm.py                 picks OpenAI vs. Ollama from .env / st.secrets
│   ├── sql_generator.py       Agent 1
│   ├── sql_executor.py        Agent 2
│   ├── chart_generator.py     Agent 3
│   ├── summarizer.py          Agent 4
│   └── error_memory.py        cross-run fix log
└── database/
    ├── init_db.py             creates & seeds the sample database
    └── schema.py               live schema introspection
```

## Known limitations & roadmap

- No automated tests yet for the SQL guardrail — a `tests/` folder proving
  it blocks `DROP TABLE` etc. is the next thing to add.
- Small local models underperform GPT-4o-mini on complex joins (see
  above).
- Single SQLite file, single user — no auth, no concurrent-write handling.
- Next: swap the sample dataset for a real one (e.g. an O-RAN dataset), and
  add a 5th agent that catches an ambiguous question and asks a clarifying
  one before generating SQL.

See [`PROJECT_REPORT.txt`](PROJECT_REPORT.txt) for the full breakdown.
