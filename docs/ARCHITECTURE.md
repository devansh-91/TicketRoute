# Architecture

TicketRoute is a two-layer intern demo:

1. **Always-on local models** (sklearn) so the UI works with no cloud key.
2. **Optional LLM** (Groq preferred, Ollama fallback) for a ticket-specific reply and a second opinion on department/urgency.

```
                 ┌──────────────┐
  ticket text ──►│ language.py  │── en / hi / hinglish
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │  sklearn     │  TF-IDF + logreg
                 │  dept + urg  │  models/*.joblib
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │  similar.py  │  TF-IDF cosine vs data/tickets.csv
                 └──────┬───────┘
                        ▼
                 ┌──────────────┐
                 │  llm.py      │  Groq → else Ollama → else templates
                 └──────┬───────┘
                        ▼
              Streamlit (app.py)   FastAPI (api.py)
                        ▼
              data/overrides.csv (officer corrections)
```

## Process

`predict_ticket(text, use_llm=True)` in `ticketroute/predict.py`:

- Normalise text, detect language.
- Load `models/department.joblib` and `models/urgency.joblib`.
- Confidence = min(dept_proba, urg_proba). Below `ABSTAIN_THRESHOLD` (0.45) → `needs_human`.
- Draft a template reply that quotes the ticket.
- If `use_llm`, call Groq with a JSON schema (department must match taxonomy). On success, replace labels + reply.

## Why not LLM-only

- Groq keys and rate limits fail. Demo day still needs a classifier.
- Sklearn is millisecond-local on CPU.
- LLM replies are the visible quality jump for HCL.

## Data

`data/tickets.csv` is synthetic (en / hi / hinglish × departments × urgencies). Train/test split is in `ticketroute/train.py`. Metrics in `reports/metrics.json` are **not** production numbers.

## Security

- `.env` is gitignored (also `.env.*`).
- Only `.env.example` is in git.
- Overrides and secrets never go to GitHub.
