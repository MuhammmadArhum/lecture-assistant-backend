# Lecture-Assistant Agent

A LangGraph agent that takes a lecture topic through research → synthesis →
final brief, with two real human-in-the-loop checkpoints (Plan Review and
Fact Verification), full per-node structured logging, and one-click .pptx
slide export.

Example topic used throughout this scaffold: **"The Hidden Engineering of
Ant Colonies"** — original content, not drawn from the assignment PDF.

## Setup

1. Copy `.env.example` to `.env` and fill in `GROQ_API_KEY` (and
   optionally `TAVILY_API_KEY` — without it, the Search Node uses a small
   built-in stub result set so the whole graph still runs end to end).

2. Backend (from the project root):
   ```
   pip install -r requirements.txt
   uvicorn backend.main:app --reload
   ```

3. Frontend (from `project_root/frontend`):
   ```
   npm install
   npm run dev
   ```
   Open http://localhost:3000.

## How the pieces fit together

- `backend/graph/build_graph.py` wires the 10 nodes with a `MemorySaver`
  checkpointer so a paused run's state survives between HTTP requests.
- `backend/graph/nodes/hitl_plan_review_node.py` and
  `fact_verification_node.py` call `langgraph.types.interrupt()` — the graph
  genuinely halts there. `POST /resume` sends `Command(resume=decision)` to
  continue it; there is no timeout or auto-approve path.
- Every node writes one JSON line to `backend/logs/run_log.jsonl` via
  `backend/logging_utils.py` (timestamp, inputs, prompt used, output, model
  settings, human decision). Fetch a single run's lines with
  `GET /logs/{thread_id}`.
- `backend/export/pptx_builder.py` turns a Final Brief JSON object into a
  themed `.pptx` (`POST /export/pptx`), independent of `main.py`.
- If `GROQ_API_KEY` isn't set, or a model call fails to return valid
  JSON, each LLM-backed node falls back to a deterministic offline stub so
  the graph is still runnable for a quick smoke test.

## API

| Endpoint | Purpose |
|---|---|
| `POST /runs` | Start a run: `{topic, audience, target_minutes, groq_api_key?, tavily_api_key?}` → runs until the first interrupt |
| `POST /resume` | `{thread_id, status, notes?, accepted_ids?}` → resumes a paused run |
| `GET /runs/{thread_id}` | Current graph state snapshot |
| `GET /logs/{thread_id}` | Structured log lines for one run |
| `POST /export/pptx` | Final brief JSON → downloadable `.pptx` |

## Bring-your-own API key

The app is designed to run without the server ever holding a shared,
billable API key. Click the 🔑 button (top-left) in the frontend to enter
your own Groq key (required — get a free one at
[console.groq.com/keys](https://console.groq.com/keys)) and, optionally, a
Tavily key for live web search. Keys are kept in the browser's
`localStorage` only, sent to the backend with each `/runs` call, threaded
through the LangGraph state for that run, and never written to disk. If you
*do* want a shared server-side fallback (e.g. for your own personal
deployment), set `GROQ_API_KEY` / `TAVILY_API_KEY` as env vars on the
backend — a user-supplied key always takes priority over it.

## Deploying: backend on Render, frontend on Vercel

See the step-by-step walkthrough in the chat where this was set up, or in
short:

1. Push this whole project to a GitHub repo (keep `backend/` and
   `frontend/` as siblings at the repo root).
2. **Render** → New Web Service → point at the repo → root directory =
   repo root → build command `pip install -r requirements.txt` → start
   command `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`. A
   `render.yaml` blueprint is included if you'd rather use "New +" →
   "Blueprint". Set `FRONTEND_ORIGIN` once you know your Vercel URL.
3. **Vercel** → New Project → same repo → root directory = `frontend` →
   framework preset Next.js (auto-detected) → env var
   `NEXT_PUBLIC_API_BASE` = your Render URL.
4. Update `FRONTEND_ORIGIN` on Render to your Vercel URL and redeploy the
   backend so CORS allows it.

## Notes

- Rename the ZIP per your course's rule before submitting, e.g.
  `yourname_Assignment1.zip`.
- `backend/logs/` is gitignored but kept in the zip via `.gitkeep` so the
  directory exists on a fresh checkout.
