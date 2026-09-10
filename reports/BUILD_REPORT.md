TicketRoute rebuild report
==========================
Date: 10 Sep 2026
Folder: /home/warrior/hcl project
GitHub: https://github.com/devansh-91/TicketRoute  (public)

WHAT CHANGED vs v0 sklearn-only
-------------------------------
- Groq is the preferred LLM (GROQ_API_KEY in .env, never committed)
- Ollama is the fallback if Groq is missing
- LLM writes a ticket-specific reply and can override department/urgency
- Similar-ticket retrieval (TF-IDF cosine) on the labelled CSV
- Template replies now quote the ticket text so sklearn-only is not generic
- FastAPI /health reports llm backends
- pytest: 11 passed

LIVE CHECKS (this machine)
--------------------------
Streamlit http://127.0.0.1:8501  health 200
API      http://127.0.0.1:8000/health  ok
POST /predict use_llm=false:

Hinglish "Mera order nahi aaya, payment kat gaya."
  dept=Product / Order / Delivery  urg=P1  lang=hinglish

Hindi account takeover
  dept=Account / KYC / Login  urg=P1  lang=hi

GROQ KEY
--------
Not present in the environment at rebuild time. UI defaults LLM toggle OFF
until GROQ_API_KEY is in .env. Ollama is up but a 9.7B CPU model was already
loaded and timed out — do not block the demo on it.

Paste GROQ_API_KEY into /home/warrior/hcl project/.env and restart Streamlit
to switch the sidebar to Groq.
