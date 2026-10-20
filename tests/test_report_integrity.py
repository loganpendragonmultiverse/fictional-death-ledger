import json

import pytest
from test_core_cli import ledger

from fictional_death_ledger.cli import main
from fictional_death_ledger.core import load_ledger, render_markdown, report


def write(tmp_path, data):
    path = tmp_path / "ledger.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.mark.parametrize("version", [True, False, 1.0, [], {}])
def test_versions_are_integers(tmp_path, version):
    data = ledger()
    data["version"] = version
    with pytest.raises(ValueError):
        load_ledger(write(tmp_path, data))


def test_duplicate_json_keys(tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text('{"version":1,"version":1,"claims":[]}')
    assert main([str(path)]) == 2
    assert "duplicate JSON key" in capsys.readouterr().err


def test_output_is_exclusive_even_for_dangling_symlink(tmp_path):
    path = write(tmp_path, ledger())
    original = path.read_bytes()
    output = tmp_path / "report.md"
    assert main([str(path), "--output", str(output)]) == 0
    content = output.read_bytes()
    assert main([str(path), "--output", str(output)]) == 2
    assert output.read_bytes() == content
    assert path.read_bytes() == original
    link = tmp_path / "link"
    missing = tmp_path / "missing"
    try:
        link.symlink_to(missing)
    except (OSError, NotImplementedError):
        return  # Windows runners may not grant symlink creation privileges.
    assert main([str(path), "--output", str(link)]) == 2
    assert not missing.exists()


def test_empty_ledger(tmp_path):
    data = ledger()
    data["characters"] = []
    result = report(load_ledger(write(tmp_path, data)))
    assert result["characters"] == []
    assert "Status through" in render_markdown(result)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(milestones=[{}]),
        lambda d: d.update(milestones=[" "]),
        lambda d: d["characters"][0].update(id=" "),
        lambda d: d["characters"][0].update(name=""),
        lambda d: d["characters"][0]["events"][0].update(status=[]),
        lambda d: d["characters"][0]["events"][0].update(certainty={}),
        lambda d: d["characters"][0]["events"][0].update(cause=[]),
        lambda d: d["characters"][0]["events"][0].update(witnesses="Ivo"),
        lambda d: d["characters"][0]["events"][0].update(witnesses=[None]),
        lambda d: d["characters"][0]["events"][0].update(witnesses=[" "]),
    ],
)
def test_malformed_detail_fields(tmp_path, mutate):
    data = ledger()
    mutate(data)
    assert main([str(write(tmp_path, data))]) == 2


def test_markdown_is_literal_and_json_is_unchanged(tmp_path):
    from fictional_death_ledger.core import changes

    data = ledger()
    data["characters"][0]["name"] = "<script>bad</script>\n# Forged"
    data["characters"][0]["events"][-1].update(
        cause="[click](javascript:x)", witnesses=["**fake**"]
    )
    loaded = load_ledger(write(tmp_path, data))
    result = report(loaded)
    for markdown in [
        render_markdown(result),
        render_markdown(changes(loaded, "Chapter 1", "Chapter 2")),
    ]:
        assert "<script>" not in markdown and "\n# Forged" not in markdown
        assert r"\[click\]" in markdown and r"\*\*fake\*\*" in markdown
    assert result["characters"][0]["name"] == data["characters"][0]["name"]
