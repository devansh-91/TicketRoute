# TicketRoute — short HCL report

**Project:** P_117 AI-Powered Customer Support Ticket Classifier  
**Working name:** TicketRoute  
**Date:** 10 Sep 2026  
**Repo:** https://github.com/devansh-91/TicketRoute

## Problem

Support queues mix English, Hindi, and Hinglish. Wrong first-hop department misses SLA. We classify department + urgency, tag language, draft a first reply, and abstain to a human when unsure.

## Data

Synthetic labelled CSV (`data/tickets.csv`, n=1200): 6 routeable departments × 3 languages × P1–P4, plus channel and timestamp. No private inboxes. Split 70/15/15 by department.

## Model

- Language: script + Hinglish lexicon; other Indic scripts → `other` (human).
- Department / urgency: TF-IDF + logistic regression (CPU). Abstain below 0.45 → `Other / Unknown`.
- Reply: templates with locked SLA hours; Groq (or Ollama) only polishes tone.
- Similar tickets: TF-IDF cosine.
- Inbox / overrides: SQLite (`data/ticketroute.db`).

MuRIL fine-tune was specified for a later week on Colab; it is not in this laptop demo (8–16 GB RAM, no fake HF scores).

## Metrics (be honest)

See `reports/metrics.json` after `python -m ticketroute.train`.

Synthetic test accuracy is high because templates repeat. **Quote:**

- keyword baseline vs sklearn
- per-language n and accuracy
- P1 recall
- abstain / needs-human rate on live Groq tests

Do not present 100% as production F1.

## Limitations

- Synthetic data only
- LLM can still drift; we reject replies that drop the SLA number
- No live email/WhatsApp ingest (out of scope)
- Department names were truncated in Streamlit `metric()`; UI now uses full text

## Demo success bar

Paste a Hinglish billing/order complaint → department, urgency, language-matched reply, confidence, one-click override, language-sliced metrics in the UI.
