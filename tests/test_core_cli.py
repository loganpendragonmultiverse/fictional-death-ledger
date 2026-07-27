import json

import pytest

from fictional_death_ledger.cli import main
from fictional_death_ledger.core import load_ledger, render_markdown, report


def ledger():
    return {
        "version": 1,
        "milestones": ["Chapter 1", "Chapter 2"],
        "characters": [
            {
                "id": "mara",
                "name": "Mara",
                "events": [
                    {"milestone": "Chapter 1", "status": "alive"},
                    {
                        "milestone": "Chapter 2",
                        "status": "dead",
                        "certainty": "confirmed",
                        "cause": "collapse",
                        "witnesses": ["Ivo"],
                    },
                ],
            }
        ],
    }


def test_spoiler_boundary_and_render():
    early = report(ledger(), "Chapter 1")
    assert early["characters"][0]["status"] == "alive"
    final = report(ledger())
    assert final["counts"]["dead"] == 1
    assert "cause: collapse" in render_markdown(final)
    with pytest.raises(ValueError, match="unknown"):
        report(ledger(), "Chapter 9")


def test_load_validation(tmp_path):
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps(ledger()), encoding="utf-8")
    assert load_ledger(path)["characters"][0]["id"] == "mara"
    data = ledger()
    data["characters"][0]["events"].reverse()
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="order"):
        load_ledger(path)


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ({"version": 2}, ValueError),
        ({"version": 1, "milestones": [], "characters": []}, ValueError),
        ({"version": 1, "milestones": ["A"], "characters": {}}, TypeError),
        ({"version": 1, "milestones": ["A"], "characters": [None]}, TypeError),
        (
            {
                "version": 1,
                "milestones": ["A"],
                "characters": [{"id": "x", "name": "X", "events": []}],
            },
            ValueError,
        ),
        (
            {
                "version": 1,
                "milestones": ["A"],
                "characters": [
                    {"id": "x", "name": "X", "events": [{"milestone": "B", "status": "alive"}]}
                ],
            },
            ValueError,
        ),
        (
            {
                "version": 1,
                "milestones": ["A"],
                "characters": [
                    {"id": "x", "name": "X", "events": [{"milestone": "A", "status": "ghost"}]}
                ],
            },
            ValueError,
        ),
    ],
)
def test_rejects_invalid_ledger_shapes(tmp_path, payload, error):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(error):
        load_ledger(path)


def test_rejects_duplicate_character(tmp_path):
    data = ledger()
    data["characters"].append(data["characters"][0].copy())
    path = tmp_path / "duplicate.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_ledger(path)


def test_cli_json_and_safe_output(tmp_path, capsys):
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps(ledger()), encoding="utf-8")
    assert main([str(path), "--through", "Chapter 1", "--format", "json"]) == 0
    assert '"alive": 1' in capsys.readouterr().out
    output = tmp_path / "report.md"
    output.write_text("keep", encoding="utf-8")
    assert main([str(path), "--output", str(output)]) == 2
