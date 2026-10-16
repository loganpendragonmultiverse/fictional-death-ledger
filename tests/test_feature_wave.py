import json

import pytest

from fictional_death_ledger.cli import main
from fictional_death_ledger.core import changes, render_markdown, report


def ledger():
    def character(name, events):
        return {"id": name, "name": name, "events": events}

    def event(at, status, **rest):
        return {"milestone": at, "status": status, **rest}

    return {
        "version": 1,
        "milestones": ["A", "B", "FUTURE_LABEL"],
        "characters": [
            character(
                "Changed",
                [
                    event("A", "alive"),
                    event("B", "dead", cause="fall"),
                    event(
                        "FUTURE_LABEL", "alive", cause="FUTURE_CAUSE", witnesses=["FUTURE_WITNESS"]
                    ),
                ],
            ),
            character(
                "Certain",
                [
                    event("A", "dead", certainty="suspected"),
                    event("B", "dead", certainty="confirmed"),
                ],
            ),
            character("Same", [event("A", "alive"), event("B", "alive")]),
            character("New", [event("B", "alive")]),
            character("FUTURE_CHARACTER", [event("FUTURE_LABEL", "dead")]),
        ],
    }


def test_changes_and_no_future_leaks(tmp_path, capsys):
    data = ledger()
    result = changes(data, "A", "B")
    rows = {x["name"]: x for x in result["changes"]}
    assert set(rows) == {"Changed", "Certain", "New"}
    assert rows["Changed"]["before"]["status"] == "alive"
    assert rows["Changed"]["after"]["status"] == "dead"
    assert rows["Certain"]["before"]["certainty"] == "suspected"
    assert rows["Certain"]["after"]["certainty"] == "confirmed"
    assert rows["New"]["before"] is None
    assert "FUTURE" not in json.dumps(result) + render_markdown(result)
    assert report(data, "A")["counts"]["alive"] == 2
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps(data))
    assert main([str(path), "--between", "A", "B", "--format", "json"]) == 0
    assert "FUTURE" not in capsys.readouterr().out
    assert main([str(path), "--between", "A", "B", "--output", str(tmp_path / "changes.md")]) == 0


@pytest.mark.parametrize("early,late", [("B", "A"), ("A", "A"), ("unknown", "B"), ("A", "unknown")])
def test_invalid_comparison(early, late):
    with pytest.raises(ValueError):
        changes(ledger(), early, late)


def test_revival_details_and_no_changes():
    data = ledger()
    data["characters"][0]["events"][0]["status"] = "dead"
    data["characters"][0]["events"][1].update(status="alive", witnesses=["Observer"])
    result = changes(data, "A", "B")
    changed = next(row for row in result["changes"] if row["id"] == "Changed")
    assert changed["before"]["status"] == "dead"
    assert changed["after"]["status"] == "alive"
    assert "witnesses: Observer" in render_markdown(result)
    data["characters"] = [data["characters"][2]]
    assert changes(data, "A", "B")["changes"] == []
