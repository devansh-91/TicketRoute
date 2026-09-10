from ticketroute.store import analytics, insert_ticket, list_tickets, save_override


def test_sqlite_roundtrip(tmp_path, monkeypatch):
    import ticketroute.store as store

    monkeypatch.setattr(store, "DB", tmp_path / "t.db")
    pred = {
        "text": "hello",
        "channel": "web",
        "language": "en",
        "department": "Feedback / General",
        "urgency": "P4",
        "confidence": 0.9,
        "needs_human": False,
        "source": "sklearn",
        "suggested_reply": "thanks",
    }
    tid = insert_ticket(pred)
    assert tid >= 1
    rows = list_tickets()
    assert rows[0]["id"] == tid
    save_override(tid, "Feedback / General", "P4", "Billing & Payments", "P3", "fix")
    a = analytics()
    assert a["n_tickets"] == 1
    assert a["n_overrides"] == 1
