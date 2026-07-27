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
