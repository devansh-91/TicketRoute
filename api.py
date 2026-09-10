from fastapi import FastAPI
from pydantic import BaseModel, Field

from ticketroute.llm import backends
from ticketroute.predict import predict_ticket

app = FastAPI(
    title="TicketRoute",
    version="1.0.0",
    description="HCL P_117 multilingual support ticket classifier + router",
)


class TicketIn(BaseModel):
    text: str = Field(..., min_length=1)
    use_llm: bool = True


@app.get("/health")
def health():
    b = backends()
    return {"ok": True, "service": "ticketroute", "llm": b}


@app.post("/predict")
def predict(body: TicketIn):
    return predict_ticket(body.text, use_llm=body.use_llm)
