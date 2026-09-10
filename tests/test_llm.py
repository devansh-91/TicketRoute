from ticketroute.llm import _extract_json, sla_mentioned


def test_extract_ok():
    assert _extract_json('{"suggested_reply":"hi"}')["suggested_reply"] == "hi"


def test_sla_p1_not_fooled_by_prefix():
    assert sla_mentioned("P1 (Critical). We will update in 24 hours.", 1) is False
    assert sla_mentioned("P1 (Critical). Update within 1 hour.", 1) is True


def test_sla_p2_not_fooled_by_24():
    assert sla_mentioned("We will reply in 24 hours.", 4) is False
    assert sla_mentioned("Payments team 4 hours me update degi.", 4) is True
