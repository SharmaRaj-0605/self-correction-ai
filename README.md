# Self-Correcting Multi-Agent AI

A multi-agent AI app that drafts an answer, reviews it, fact-checks it, and
rewrites it until it meets a quality score, with a hard limit on correction
rounds so it never loops forever.

**Stack:** FastAPI (backend) · Streamlit (frontend) · Redis (cache) ·
Google Gemini (LLM) · Pydantic (validation) · one Dockerfile for everything.

---

## How it works

```
User → Guardrails → Planner → Researcher → Analyst → Synthesizer
     → Critic → Fact Checker → Judge ──approved──→ Final answer
                                  │
                               revise
                                  ↓
                          Correction Agent → (back to Critic)
```

| Agent | Job |
|---|---|
| Planner | Breaks the task into subtasks |
| Researcher | Collects facts, examples and caveats |
| Analyst | Finds key points, tradeoffs and weaknesses |
| Synthesizer | Writes the first draft |
| Critic | Scores the draft (0–10) and lists problems |
| Fact Checker | Flags questionable claims, gives a confidence value |
| Judge | Approves the draft or asks for a revision |
| Correction Agent | Rewrites the draft using the feedback |

The loop stops when the Judge approves **and** the score is at least
`MIN_ACCEPT_SCORE`, or after `MAX_ITERATIONS` rounds, whichever comes first.

All agents are roles on the same Gemini model, not separate paid services.

---

## Architecture

Everything runs in a **single container**:

```
Browser → Streamlit (public, on $PORT)
             → FastAPI  (127.0.0.1:8000, internal only)
                   → Redis (127.0.0.1:6379, bundled cache)
```

- Only Streamlit is reachable from the internet. The API is not exposed.
- Redis is installed inside the image. If Redis is unavailable, the backend
  falls back to a small in-memory cache instead of failing.
- Gemini calls are retried with exponential backoff on temporary errors
  (429, 500, 502, 503, 504). An optional fallback model can be used if the
  main model keeps failing.
- If any of the three processes dies, the container exits so the host
  (for example Render) restarts it.

---

## Project structure

```
Dockerfile              single image: Streamlit + FastAPI + Redis
docker-compose.yml      local testing only
requirements.txt
.env.example            template for your settings

frontend/
  app.py                Streamlit UI

backend/app/
  main.py               FastAPI app and /health
  api/routes.py         POST /api/v1/tasks
  core/config.py        settings from environment variables
  core/guardrails.py    input validation and basic prompt-injection checks
  models/schemas.py     request/response models
  services/llm.py       Gemini wrapper with retries and optional fallback
  services/cache.py     Redis cache with in-memory fallback
  agents/roles.py       the eight agents
  workflow/orchestrator.py   runs the workflow and the correction loop

```

---

## Configuration

Set these as environment variables (locally in `.env`, on Render in the
service's Environment tab). Only `GEMINI_API_KEY` is required.

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | none (required) | Your Gemini API key from Google AI Studio |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Main model used by all agents |
| `GEMINI_FALLBACK_MODEL` | empty (off) | A *different* model to try if the main one keeps failing |
| `GEMINI_MAX_RETRIES` | `5` | Retries per call on temporary Gemini errors |
| `MAX_ITERATIONS` | `3` | Maximum correction rounds |
| `MIN_ACCEPT_SCORE` | `8.0` | Score needed for the Judge to approve |
| `USE_WEB_SEARCH` | `false` | Enable Google Search grounding (if your key supports it) |
| `CACHE_TTL_SECONDS` | `900` | How long finished results stay cached |
| `MAX_INPUT_CHARS` | `8000` | Maximum prompt length |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | Only change this to use an external Redis |

Never put your API key in code or commit `.env`. It is already in `.gitignore`.

---

## Run locally

Requirements: Docker Desktop and a Gemini API key.

1. Copy `.env.example` to `.env` (PowerShell: `Copy-Item .env.example .env`).
2. Put your key in it:

   ```
   GEMINI_API_KEY=your_key_here
   ```

3. Start the app:

   ```
   docker compose up --build
   ```

4. Open **http://localhost:8501**

Stop with `docker compose down`. After changing code, run
`docker compose up --build` again so the image is rebuilt.
