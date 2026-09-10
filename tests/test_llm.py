from ticketroute.llm import _extract_json


def test_extract_ok():
    assert _extract_json('{"suggested_reply":"hi"}')["suggested_reply"] == "hi"
