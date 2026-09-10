from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ticketroute.llm import backends
from ticketroute.predict import predict_ticket
from ticketroute.store import analytics, get_ticket, list_overrides, list_tickets, save_override

app = FastAPI(
    title="TicketRoute",
    version="1.1.0",
    description="HCL P_117 multilingual support ticket classifier + router",
)


class TicketIn(BaseModel):
    text: str = Field(..., min_length=1)
    use_llm: bool = True
    channel: str = "web"
    ext_id: str | None = None
    persist: bool = True


class OverrideIn(BaseModel):
    department: str
    urgency: str
    note: str = ""


@app.get("/health")
def health():
    return {"ok": True, "service": "ticketroute", "llm": backends()}


@app.post("/predict")
def predict(body: TicketIn):
    return predict_ticket(
        body.text,
        use_llm=body.use_llm,
        channel=body.channel,
        ext_id=body.ext_id,
        persist=body.persist,
    )


@app.get("/tickets")
def tickets(
    department: str | None = None,
    language: str | None = None,
    urgency: str | None = None,
    needs_human: bool | None = None,
    limit: int = 100,
):
    return list_tickets(department, language, urgency, needs_human, limit)


@app.get("/tickets/{ticket_id}")
def ticket_one(ticket_id: int):
    row = get_ticket(ticket_id)
    if not row:
        raise HTTPException(404, "not found")
    return row


@app.post("/tickets/{ticket_id}/override")
def ticket_override(ticket_id: int, body: OverrideIn):
    row = get_ticket(ticket_id)
    if not row:
        raise HTTPException(404, "not found")
    save_override(
        ticket_id,
        row.get("department") or "",
        row.get("urgency") or "",
        body.department,
        body.urgency,
        body.note,
    )
    return get_ticket(ticket_id)


@app.get("/overrides")
def overrides(limit: int = 100):
    return list_overrides(limit)


@app.get("/analytics")
def analytics_view():
    return analytics()
