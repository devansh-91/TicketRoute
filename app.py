from __future__ import annotations

import io
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from ticketroute.llm import backends
from ticketroute.predict import predict_ticket
from ticketroute.store import analytics, list_overrides, list_tickets, save_override
from ticketroute.taxonomy import CHANNELS, DEPARTMENTS, LANGUAGES, SLA_HOURS, URGENCY, URGENCY_LABEL

ROOT = Path(__file__).resolve().parent

st.set_page_config(page_title="TicketRoute — HCL P_117", layout="wide")
st.title("TicketRoute")
st.caption("HCL P_117 · en / hi / hinglish · inbox + SLA · sklearn labels, LLM polish")

info = backends()
with st.sidebar:
    st.subheader("LLM backend")
    st.write(f"Active: **{info['active']}**")
    if info["model"]:
        st.write(f"Model: `{info['model']}`")
    st.write(f"Groq key: {'yes' if info['groq'] else 'no'}")
    st.write(f"Ollama: {'up' if info['ollama'] else 'down'}")
    use_llm = st.toggle("LLM polish reply (keep local labels)", value=bool(info["groq"]))
    persist = st.toggle("Save to inbox (SQLite)", value=True)
    channel = st.selectbox("Channel", CHANNELS, index=CHANNELS.index("web") if "web" in CHANNELS else 0)
    st.caption("Labels come from sklearn. LLM only rewrites the reply and must keep SLA hours.")


def show_result(pred: dict, key: str) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.write("**Language**")
    c1.write(pred["language"])
    c2.write("**Department**")
    c2.write(pred["department"])
    c3.write("**Urgency**")
    c3.write(f"{pred['urgency']} ({URGENCY_LABEL.get(pred['urgency'], '')})")
    c4.write("**Confidence**")
    c4.write(str(pred["confidence"]))
    sla = pred.get("sla_hours") or SLA_HOURS.get(pred["urgency"], 24)
    st.caption(
        f"source={pred.get('source')} · llm={pred.get('llm_backend')} · "
        f"SLA {sla}h · ticket_id={pred.get('ticket_id', '—')}"
    )
    if pred.get("llm_error"):
        st.warning(f"LLM fallback: {pred['llm_error']}")
    if pred["needs_human"]:
        st.warning("Abstain / safety — send to human.")
    else:
        st.success("Auto-route suggested.")
    if pred.get("rationale"):
        st.write("**Why:**", pred["rationale"])
    if pred.get("explain"):
        st.caption("Tokens: " + ", ".join(pred["explain"]))
    st.subheader("Suggested reply")
    st.write(pred["suggested_reply"])
    with st.expander("Local classifier top-3 + template"):
        st.write("Department", pred.get("department_top3"))
        st.write("Urgency", pred.get("urgency_top3"))
        st.write(pred.get("template_reply"))
    sims = pred.get("similar") or []
    if sims:
        st.subheader("Similar past tickets")
        st.dataframe(pd.DataFrame(sims), width="stretch")

    st.subheader("Officer override")
    oc1, oc2 = st.columns(2)
    try:
        di = DEPARTMENTS.index(pred["department"])
    except ValueError:
        di = DEPARTMENTS.index("Other / Unknown") if "Other / Unknown" in DEPARTMENTS else 0
    try:
        ui = URGENCY.index(pred["urgency"])
    except ValueError:
        ui = 2
    od = oc1.selectbox("Correct department", DEPARTMENTS, index=di, key=f"d-{key}")
    ou = oc2.selectbox("Correct urgency", URGENCY, index=ui, key=f"u-{key}")
    note = st.text_input("Override note", key=f"n-{key}")
    if st.button("Save override", key=f"b-{key}"):
        tid = pred.get("ticket_id")
        if tid:
            save_override(int(tid), pred["department"], pred["urgency"], od, ou, note)
            st.toast(f"Override saved on ticket {tid}")
        else:
            st.info("Classify with ‘Save to inbox’ on to store an override.")


tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Classify", "Inbox", "CSV batch", "Analytics", "Metrics"]
)

with tab1:
    sample = "Mera order nahi aaya, payment kat gaya."
    text = st.text_area("Ticket text", value=sample, height=140, key="ticket_text")
    if st.button("Classify", type="primary") and text.strip():
        with st.spinner("Classifying…"):
            pred = predict_ticket(
                text.strip(),
                use_llm=use_llm,
                channel=channel,
                persist=persist,
            )
        st.session_state["last"] = pred
        st.session_state["last_text"] = text.strip()
    if st.session_state.get("last"):
        if st.session_state.get("last_text") and st.session_state["last_text"] != text.strip():
            st.info("Text changed — click Classify again for a new prediction.")
        show_result(st.session_state["last"], f"single-{st.session_state['last'].get('ticket_id', 'x')}")

with tab2:
    f1, f2, f3, f4 = st.columns(4)
    fd = f1.selectbox("Dept filter", ["(all)"] + DEPARTMENTS)
    fl = f2.selectbox("Lang filter", ["(all)"] + LANGUAGES)
    fu = f3.selectbox("Urgency filter", ["(all)"] + URGENCY)
    fh = f4.selectbox("Human", ["(all)", "needs human", "auto"])
    rows = list_tickets(
        None if fd == "(all)" else fd,
        None if fl == "(all)" else fl,
        None if fu == "(all)" else fu,
        None if fh == "(all)" else fh == "needs human",
    )
    if not rows:
        st.caption("Inbox empty — classify a ticket with Save to inbox on.")
    else:
        view = pd.DataFrame(rows)
        cols = [
            c
            for c in [
                "id",
                "created_at",
                "channel",
                "language",
                "department",
                "urgency",
                "confidence",
                "needs_human",
                "sla_hours",
                "sla_remaining_min",
                "status",
                "text",
            ]
            if c in view.columns
        ]
        st.dataframe(view[cols], width="stretch", height=360)
        pick = st.number_input("Open ticket id", min_value=1, value=int(rows[0]["id"]))
        chosen = next((r for r in rows if r["id"] == pick), None)
        if chosen:
            st.write("**Text:**", chosen.get("text"))
            st.write("**Reply:**", chosen.get("reply"))
            remaining = chosen.get("sla_remaining_min")
            if remaining is not None:
                st.write(f"**SLA remaining:** {remaining} min (due {chosen.get('due_at')})")

with tab3:
    up = st.file_uploader("CSV (columns: text, optional id/channel/timestamp)", type=["csv"])
    batch_llm = st.checkbox("LLM polish each row (slow)", value=False)
    if up is not None:
        df = pd.read_csv(up)
        text_col = "text" if "text" in df.columns else df.columns[0]
        st.write(f"Using `{text_col}` · {len(df)} rows")
        if st.button("Run batch"):
            rows_out = []
            for _, rec in df.iterrows():
                ch = str(rec["channel"]) if "channel" in df.columns and pd.notna(rec.get("channel")) else channel
                eid = str(rec["id"]) if "id" in df.columns and pd.notna(rec.get("id")) else None
                rows_out.append(
                    predict_ticket(
                        str(rec[text_col]),
                        use_llm=batch_llm,
                        channel=ch,
                        ext_id=eid,
                        persist=persist,
                    )
                )
            out = pd.DataFrame(rows_out)
            show_cols = [
                c
                for c in [
                    "ticket_id",
                    "ext_id",
                    "text",
                    "channel",
                    "language",
                    "department",
                    "urgency",
                    "confidence",
                    "needs_human",
                    "sla_hours",
                    "source",
                ]
                if c in out.columns
            ]
            st.dataframe(out[show_cols], width="stretch")
            buf = io.StringIO()
            out.to_csv(buf, index=False)
            st.download_button("Download predictions.csv", buf.getvalue(), "predictions.csv", "text/csv")

with tab4:
    a = analytics()
    st.write(a)
    ovs = list_overrides()
    st.subheader("Override audit")
    if ovs:
        st.dataframe(pd.DataFrame(ovs), width="stretch")
    else:
        st.caption("No overrides yet.")

with tab5:
    metrics = ROOT / "reports" / "metrics.json"
    if metrics.exists():
        st.json(metrics.read_text(encoding="utf-8"))
    else:
        st.info("Train first: python -m ticketroute.train")
    st.caption(
        "Synthetic held-out scores are high because templates are small. "
        "Compare to the keyword baseline in metrics.json. Do not quote 100% to HCL."
    )
