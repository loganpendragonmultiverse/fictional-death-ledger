from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

STATUSES = {"alive", "dead", "missing", "unknown"}
CERTAINTIES = {"confirmed", "reported", "suspected", "ambiguous"}


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _text(value: str) -> str:
    """Keep supplied text literal in a single Markdown line."""
    value = html.escape(" ".join(value.splitlines()), quote=False)
    return re.sub(r"([\\`*_{}\[\]()#+.!|~>-])", r"\\\1", value)


def load_ledger(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_object)
    if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1:
        raise ValueError("ledger must be a version 1 object")
    milestones = data.get("milestones")
    characters = data.get("characters")
    if (
        not isinstance(milestones, list)
        or not milestones
        or not all(isinstance(item, str) and item.strip() for item in milestones)
        or len(set(milestones)) != len(milestones)
    ):
        raise ValueError("milestones must be a non-empty unique string list")
    if not isinstance(characters, list):
        raise TypeError("characters must be a list")
    seen: set[str] = set()
    for character in characters:
        if (
            not isinstance(character, dict)
            or not isinstance(character.get("id"), str)
            or not isinstance(character.get("name"), str)
        ):
            raise TypeError("each character requires string id and name")
        if not character["id"].strip() or not character["name"].strip():
            raise ValueError("character id and name must not be blank")
        if character["id"] in seen:
            raise ValueError(f"duplicate character id: {character['id']}")
        events = character.get("events", [])
        if not isinstance(events, list) or not events:
            raise ValueError(f"character {character['id']} requires events")
        last = -1
        for event in events:
            if not isinstance(event, dict) or event.get("milestone") not in milestones:
                raise ValueError(f"character {character['id']} has an invalid milestone")
            position = milestones.index(event["milestone"])
            if position <= last:
                raise ValueError(f"character {character['id']} events must follow milestone order")
            if (
                not isinstance(event.get("status"), str)
                or event["status"] not in STATUSES
                or not isinstance(event.get("certainty", "confirmed"), str)
                or event.get("certainty", "confirmed") not in CERTAINTIES
            ):
                raise ValueError(f"character {character['id']} has an invalid status or certainty")
            if "cause" in event and not isinstance(event["cause"], str):
                raise TypeError("event cause must be a string")
            witnesses = event.get("witnesses", [])
            if not isinstance(witnesses, list) or not all(
                isinstance(witness, str) and witness.strip() for witness in witnesses
            ):
                raise TypeError("event witnesses must be a list of nonblank strings")
            last = position
        seen.add(character["id"])
    return data


def report(data: dict[str, Any], through: str | None = None) -> dict[str, Any]:
    milestones = data["milestones"]
    if through is not None and through not in milestones:
        raise ValueError(f"unknown milestone: {through}")
    boundary = milestones.index(through) if through else len(milestones) - 1
    characters = []
    for character in data["characters"]:
        events = [
            event
            for event in character["events"]
            if milestones.index(event["milestone"]) <= boundary
        ]
        if not events:
            continue
        characters.append(
            {
                "id": character["id"],
                "name": character["name"],
                "status": events[-1]["status"],
                "certainty": events[-1].get("certainty", "confirmed"),
                "events": events,
            }
        )
    characters.sort(key=lambda item: item["name"].casefold())
    counts = Counter(item["status"] for item in characters)
    return {
        "version": 1,
        "through": milestones[boundary],
        "counts": {status: counts.get(status, 0) for status in sorted(STATUSES)},
        "characters": characters,
    }


def changes(data: dict[str, Any], earlier: str, later: str) -> dict[str, Any]:
    milestones = data["milestones"]
    if earlier not in milestones or later not in milestones:
        raise ValueError("unknown comparison milestone")
    if milestones.index(earlier) >= milestones.index(later):
        raise ValueError("comparison requires ordered earlier and later milestones")
    before = {row["id"]: row for row in report(data, earlier)["characters"]}
    after = report(data, later)["characters"]

    def state(row: dict[str, Any]) -> dict[str, Any]:
        event = row["events"][-1]
        return {
            key: event.get(key, default)
            for key, default in (
                ("status", "unknown"),
                ("certainty", "confirmed"),
                ("cause", ""),
                ("witnesses", []),
            )
        }

    rows = []
    for row in after:
        previous = state(before[row["id"]]) if row["id"] in before else None
        current = state(row)
        if previous != current:
            rows.append(
                {"id": row["id"], "name": row["name"], "before": previous, "after": current}
            )
    return {"version": 2, "mode": "changes", "earlier": earlier, "later": later, "changes": rows}


def render_changes(result: dict[str, Any]) -> str:
    lines = [
        "# Fictional Death Ledger Changes",
        "",
        f"From **{_text(result['earlier'])}** through **{_text(result['later'])}**",
        "",
    ]
    for row in result["changes"]:
        before = row["before"]
        after = row["after"]
        old = f"{before['status']} ({before['certainty']})" if before else "not introduced"
        detail = f"{after['status']} ({after['certainty']})"
        if after["cause"]:
            detail += f"; cause: {_text(after['cause'])}"
        if after["witnesses"]:
            detail += "; witnesses: " + ", ".join(_text(value) for value in after["witnesses"])
        lines.append(f"- **{_text(row['name'])}**: {old} → {detail}")
    return "\n".join(lines).rstrip() + "\n"


def render_markdown(result: dict[str, Any]) -> str:
    if result.get("mode") == "changes":
        return render_changes(result)
    lines = ["# Fictional Death Ledger", "", f"Status through **{_text(result['through'])}**", ""]
    for status in sorted(STATUSES):
        items = [item for item in result["characters"] if item["status"] == status]
        if not items:
            continue
        lines.extend([f"## {status.title()} ({len(items)})", ""])
        for item in items:
            event = item["events"][-1]
            details = [item["certainty"]]
            if event.get("cause"):
                details.append(f"cause: {_text(event['cause'])}")
            if event.get("witnesses"):
                details.append(
                    "witnesses: " + ", ".join(_text(value) for value in event["witnesses"])
                )
            lines.append(
                f"- **{_text(item['name'])}** — {_text(event['milestone'])}; " + "; ".join(details)
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
