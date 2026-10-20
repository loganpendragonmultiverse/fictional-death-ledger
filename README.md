# Fictional Death Ledger

[![CI](https://github.com/loganpendragonmultiverse/fictional-death-ledger/actions/workflows/ci.yml/badge.svg)](https://github.com/loganpendragonmultiverse/fictional-death-ledger/actions/workflows/ci.yml)

Fictional Death Ledger tracks character life status, causes, timing, witnesses, and uncertainty across ordered story milestones. A milestone boundary produces spoiler-controlled Markdown or JSON reports.

## Three-minute start

```bash
python -m pip install .
death-ledger examples/novel.json
death-ledger examples/novel.json --through "Chapter 8" --format json
```

Events must follow the declared milestone order. Statuses are `alive`, `dead`, `missing`, or `unknown`; certainty may be `confirmed`, `reported`, `suspected`, or `ambiguous`. Future events are omitted entirely from boundary reports.

## Boundaries

The tool validates structured author notes. It does not analyze prose, infer deaths, or decide whether an ambiguous event counts. A boundary cannot prevent spoilers already written into names or notes supplied by the user.

Requires Python 3.10 or newer. Development checks use Ruff, pytest with branch coverage, and package builds.

Part of the [Logan Pendragon Forge open-source collection](https://www.loganpendragonforge.com/open-source/). Licensed under the [MIT License](LICENSE).

## 1.1.0 - 2026-10-16

Use `death-ledger examples/novel.json --between "Chapter 1" "Chapter 8" --format json` to compare two explicit milestones in the declared order. Both boundaries must exist, and the earlier boundary must precede the later one. Comparisons include changed status, certainty, cause or witnesses and newly introduced characters; repeated identical states are omitted. Each change contains `before` (null for a new character) and `after` state. Reports contain no events or labels after the later boundary. `--through` snapshots and default complete snapshots retain their existing behavior. As with snapshots, names and details already supplied before the boundary are author-controlled and can themselves contain spoilers.

## Input and report integrity

Schema versions must be JSON integers, and duplicate object keys are rejected rather
than silently replacing earlier values. Optional report details must have their
documented string/list types. Markdown displays supplied text literally, with line
breaks flattened; JSON retains validated source values. Output creation is exclusive:
existing files are refused and existing symbolic links are checked before creation.
This is accidental-overwrite protection, not a defense against concurrent hostile
filesystem changes. Reports remain offline and do not
modify their source ledger.

Python 3.10+ on Windows, macOS and Linux is covered by the required CI matrix.
Install a release wheel with `python -m pip install path/to/release.whl`. Installed
examples and instructions are under `share/doc/fictional-death-ledger` in the environment prefix.
The [testing guide](TESTING.md) documents checks and installed-artifact acceptance.
See [contributing](CONTRIBUTING.md), [support](SUPPORT.md), and [security](SECURITY.md)
for maintenance, issue and vulnerability reporting. This small tool is maintained
through reviewed changes; no automatic truth or story interpretation is promised.
