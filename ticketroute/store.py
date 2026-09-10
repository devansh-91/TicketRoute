"""SQLite ticket inbox + override audit log."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ticketroute.taxonomy import SLA_HOURS

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "ticketroute.db"


def _conn() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ext_id TEXT,
            created_at TEXT NOT NULL,
            text TEXT NOT NULL,
            channel TEXT,
            language TEXT,
            department TEXT,
            urgency TEXT,
            confidence REAL,
            needs_human INTEGER,
            source TEXT,
            reply TEXT,
            sla_hours INTEGER,
            due_at TEXT,
            status TEXT DEFAULT 'open',
            extra TEXT
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            ts TEXT NOT NULL,
            pred_dept TEXT,
            pred_urg TEXT,
            override_dept TEXT,
            override_urg TEXT,
            note TEXT
        )
        """
    )
    con.commit()
    return con


def _due(created: datetime, urgency: str) -> tuple[int, str]:
    hours = int(SLA_HOURS.get(urgency, 24))
    due = created + timedelta(hours=hours)
    return hours, due.isoformat()


def insert_ticket(pred: dict[str, Any]) -> int:
    now = datetime.now(timezone.utc)
    hours, due = _due(now, str(pred.get("urgency") or "P3"))
    extra = {
        k: pred.get(k)
        for k in ("department_top3", "urgency_top3", "rationale", "similar", "explain")
    }
    con = _conn()
    cur = con.execute(
        """
        INSERT INTO tickets (
            ext_id, created_at, text, channel, language, department, urgency,
            confidence, needs_human, source, reply, sla_hours, due_at, status, extra
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            pred.get("ext_id"),
            now.isoformat(),
            pred.get("text") or "",
            pred.get("channel") or "web",
            pred.get("language"),
            pred.get("department"),
            pred.get("urgency"),
            pred.get("confidence"),
            1 if pred.get("needs_human") else 0,
            pred.get("source"),
            pred.get("suggested_reply"),
            hours,
            due,
            "needs_human" if pred.get("needs_human") else "open",
            json.dumps(extra, default=str),
        ),
    )
    con.commit()
    tid = int(cur.lastrowid)
    con.close()
    pred["ticket_id"] = tid
    pred["sla_hours"] = hours
    pred["due_at"] = due
    pred["created_at"] = now.isoformat()
    return tid


def list_tickets(
    department: str | None = None,
    language: str | None = None,
    urgency: str | None = None,
    needs_human: bool | None = None,
    limit: int = 200,
) -> list[dict]:
    q = "SELECT * FROM tickets WHERE 1=1"
    args: list[Any] = []
    if department:
        q += " AND department=?"
        args.append(department)
    if language:
        q += " AND language=?"
        args.append(language)
    if urgency:
        q += " AND urgency=?"
        args.append(urgency)
    if needs_human is True:
        q += " AND needs_human=1"
    elif needs_human is False:
        q += " AND needs_human=0"
    q += " ORDER BY id DESC LIMIT ?"
    args.append(limit)
    con = _conn()
    rows = [dict(r) for r in con.execute(q, args)]
    con.close()
    now = datetime.now(timezone.utc)
    for r in rows:
        r["needs_human"] = bool(r.get("needs_human"))
        due = r.get("due_at")
        r["sla_remaining_min"] = None
        if due:
            try:
                dt = datetime.fromisoformat(due)
                r["sla_remaining_min"] = int((dt - now).total_seconds() // 60)
            except ValueError:
                pass
    return rows


def get_ticket(ticket_id: int) -> dict | None:
    con = _conn()
    row = con.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
    con.close()
    return dict(row) if row else None


def save_override(
    ticket_id: int,
    pred_dept: str,
    pred_urg: str,
    override_dept: str,
    override_urg: str,
    note: str = "",
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    con = _conn()
    con.execute(
        """
        INSERT INTO overrides (ticket_id, ts, pred_dept, pred_urg, override_dept, override_urg, note)
        VALUES (?,?,?,?,?,?,?)
        """,
        (ticket_id, now, pred_dept, pred_urg, override_dept, override_urg, note),
    )
    hours = int(SLA_HOURS.get(override_urg, 24))
    row = con.execute("SELECT created_at FROM tickets WHERE id=?", (ticket_id,)).fetchone()
    created = datetime.now(timezone.utc)
    if row and row["created_at"]:
        try:
            created = datetime.fromisoformat(row["created_at"])
        except ValueError:
            pass
    hours, due = _due(created, override_urg)
    con.execute(
        """
        UPDATE tickets SET department=?, urgency=?, sla_hours=?, due_at=?, status='overridden'
        WHERE id=?
        """,
        (override_dept, override_urg, hours, due, ticket_id),
    )
    con.commit()
    con.close()


def list_overrides(limit: int = 200) -> list[dict]:
    con = _conn()
    rows = [
        dict(r)
        for r in con.execute(
            "SELECT * FROM overrides ORDER BY id DESC LIMIT ?", (limit,)
        )
    ]
    con.close()
    return rows


def analytics() -> dict:
    con = _conn()
    n = con.execute("SELECT COUNT(*) c FROM tickets").fetchone()["c"]
    by_dept = {
        r["department"]: r["c"]
        for r in con.execute(
            "SELECT department, COUNT(*) c FROM tickets GROUP BY department"
        )
    }
    by_lang = {
        r["language"]: r["c"]
        for r in con.execute(
            "SELECT language, COUNT(*) c FROM tickets GROUP BY language"
        )
    }
    n_ov = con.execute("SELECT COUNT(*) c FROM overrides").fetchone()["c"]
    n_human = con.execute(
        "SELECT COUNT(*) c FROM tickets WHERE needs_human=1"
    ).fetchone()["c"]
    con.close()
    return {
        "n_tickets": n,
        "by_department": by_dept,
        "by_language": by_lang,
        "n_overrides": n_ov,
        "override_rate": round(n_ov / n, 3) if n else 0.0,
        "needs_human_rate": round(n_human / n, 3) if n else 0.0,
    }
