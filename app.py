from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from ticketroute.llm import backends
from ticketroute.predict import predict_ticket
from ticketroute.taxonomy import DEPARTMENTS, URGENCY, URGENCY_LABEL

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "data" / "overrides.csv"

st.set_page_config(page_title="TicketRoute — HCL P_117", layout="wide")
st.title("TicketRoute")
st.caption(
    "HCL P_117 · multilingual support ticket classifier + router · en / hi / hinglish"
)

info = backends()
with st.sidebar:
    st.subheader("LLM backend")
    st.write(f"Active: **{info['active']}**")
    if info["model"]:
        st.write(f"Model: `{info['model']}`")
    st.write(f"Groq key: {'yes' if info['groq'] else 'no'}")
    st.write(f"Ollama: {'up' if info['ollama'] else 'down'}")
    if info["active"] == "none":
        st.error("No LLM. Add GROQ_API_KEY to `.env` or start Ollama.")
    elif info["active"] == "ollama":
        st.info("Using local Ollama. Drop GROQ_API_KEY in `.env` to switch to Groq.")
    use_llm = st.toggle("Use LLM for routing + reply", value=bool(info["groq"]))
    st.markdown(
        "Sklearn always runs first. LLM can override department/urgency "
        "and writes a ticket-specific reply."
    )


def append_override(row: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    new = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if new:
            w.writeheader()
        w.writerow(row)


def show_result(pred: dict, key: str) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Language", pred["language"])
    c2.metric("Department", pred["department"])
    c3.metric("Urgency", f"{pred['urgency']} ({URGENCY_LABEL.get(pred['urgency'], '')})")
    c4.metric("Confidence", pred["confidence"])
    st.caption(f"source={pred.get('source')} · llm={pred.get('llm_backend')}")
    if pred.get("llm_error"):
        st.warning(f"LLM fallback: {pred['llm_error']}")
    if pred["needs_human"]:
        st.warning("Low confidence / safety — send to human.")
    else:
        st.success("Auto-route suggested.")
    if pred.get("rationale"):
        st.write("**Why:**", pred["rationale"])
    st.subheader("Suggested reply")
    st.write(pred["suggested_reply"])
    with st.expander("Local classifier top-3"):
        st.write("Department", pred["department_top3"])
        st.write("Urgency", pred["urgency_top3"])
    sims = pred.get("similar") or []
    if sims:
        st.subheader("Similar past tickets")
        st.dataframe(pd.DataFrame(sims), use_container_width=True)

    st.subheader("Officer override")
    oc1, oc2 = st.columns(2)
    try:
        di = DEPARTMENTS.index(pred["department"])
    except ValueError:
        di = 0
    try:
        ui = URGENCY.index(pred["urgency"])
    except ValueError:
        ui = 2
    od = oc1.selectbox("Correct department", DEPARTMENTS, index=di, key=f"d-{key}")
    ou = oc2.selectbox("Correct urgency", URGENCY, index=ui, key=f"u-{key}")
    note = st.text_input("Override note", key=f"n-{key}")
    if st.button("Save override", key=f"b-{key}"):
        append_override(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "text": pred["text"][:500],
                "pred_dept": pred["department"],
                "pred_urg": pred["urgency"],
                "pred_lang": pred["language"],
                "override_dept": od,
                "override_urg": ou,
                "note": note,
                "source": pred.get("source", ""),
            }
        )
        st.toast("Override saved to data/overrides.csv")


tab1, tab2, tab3 = st.tabs(["Single ticket", "CSV batch", "Metrics / log"])

with tab1:
    sample = "Mera order nahi aaya, payment kat gaya."
    text = st.text_area("Ticket text", value=sample, height=140)
    if st.button("Classify", type="primary") and text.strip():
        with st.spinner("Classifying…"):
            pred = predict_ticket(text, use_llm=use_llm)
        st.session_state["last"] = pred
    if "last" in st.session_state:
        show_result(st.session_state["last"], "single")

with tab2:
    up = st.file_uploader("CSV with a text column", type=["csv"])
    batch_llm = st.checkbox("Use LLM on each row (slower)", value=False)
    if up is not None:
        df = pd.read_csv(up)
        col = "text" if "text" in df.columns else df.columns[0]
        st.write(f"Using column `{col}` · {len(df)} rows")
        if st.button("Run batch"):
            rows = [
                predict_ticket(str(t), use_llm=batch_llm) for t in df[col].fillna("")
            ]
            out = pd.DataFrame(rows)
            show_cols = [
                "text",
                "language",
                "department",
                "urgency",
                "confidence",
                "needs_human",
                "source",
            ]
            st.dataframe(out[show_cols], use_container_width=True)
            buf = io.StringIO()
            out.to_csv(buf, index=False)
            st.download_button(
                "Download predictions.csv",
                buf.getvalue(),
                "predictions.csv",
                "text/csv",
            )

with tab3:
    metrics = ROOT / "reports" / "metrics.json"
    if metrics.exists():
        st.json(metrics.read_text(encoding="utf-8"))
    else:
        st.info("Train first: python -m ticketroute.train")
    if LOG.exists():
        st.subheader("Overrides")
        st.dataframe(pd.read_csv(LOG), use_container_width=True)
    else:
        st.caption("No overrides yet.")
