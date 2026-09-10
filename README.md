# TicketRoute (HCL P_117)

Multilingual **customer support ticket classifier + router**.

Paste a ticket in English, Hindi, or Hinglish. The app returns:

1. language tag (`en` / `hi` / `hinglish`)
2. department
3. urgency P1–P4
4. a first reply in the ticket’s language
5. similar past tickets
6. low-confidence / safety → send to a human

This is an internship demo, not a production helpdesk.

## Why two models

| Layer | What it does |
|---|---|
| **sklearn TF-IDF + logistic regression** | Always-on local classifier. Works offline. Fast. |
| **LLM (Groq preferred, else Ollama)** | Ticket-specific reply + can override routing. |

If Groq is not configured, the app still runs on local Ollama (or sklearn-only).

## Departments

- Billing & Payments
- Account / KYC / Login
- Technical / App crash
- Product / Order / Delivery
- Abuse / Safety / Fraud
- Feedback / General

SLA: P1 1h · P2 4h · P3 24h · P4 72h

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# put GROQ_API_KEY in .env  (optional if Ollama is running)
python3 -m ticketroute.generate_data
python3 -m ticketroute.train
python3 -m pytest tests/ -q
```

## Run

```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
python3 -m uvicorn api:app --host 0.0.0.0 --port 8000
```

- UI: http://127.0.0.1:8501
- Health: http://127.0.0.1:8000/health
- Predict: `POST /predict` `{"text":"...","use_llm":true}`

## LLM backends

**Groq** (recommended): set `GROQ_API_KEY` in `.env`. Default model `openai/gpt-oss-20b` (this account’s Groq catalogue; override with `GROQ_MODEL`).

**Ollama** fallback: any local chat model. Default `llama3.2:3b` at `http://127.0.0.1:11434`.

`.env` is gitignored. Never commit keys.

## Honest metrics

Held-out accuracy on the synthetic CSV is near 1.0 because the templates are small. Do **not** quote that as production F1. Next step is noisy real tickets + a MuRIL encoder.

## Repo

https://github.com/devansh-91/TicketRoute
