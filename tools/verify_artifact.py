"""Verify a release archive by installing it outside the source checkout."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    artifact = Path(sys.argv[1]).resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="fictional-death-ledger-installed-") as temporary:
        root = Path(temporary)
        prefix = root / "venv"
        subprocess.run([sys.executable, "-m", "venv", str(prefix)], check=True)
        binary = prefix / ("Scripts" if os.name == "nt" else "bin")
        python = binary / ("python.exe" if os.name == "nt" else "python")
        executable = binary / ("death-ledger.exe" if os.name == "nt" else "death-ledger ".strip())
        environment = dict(os.environ)
        environment.pop("PYTHONPATH", None)
        environment["PYTHONNOUSERSITE"] = "1"

        def run(arguments: list[str], expected: int = 0) -> str:
            result = subprocess.run(
                arguments, cwd=root, env=environment, text=True, capture_output=True, check=False
            )
            assert result.returncode == expected, (arguments, result.stdout, result.stderr)
            assert "Traceback" not in result.stderr
            return result.stdout

        run([str(python), "-m", "pip", "install", "--no-deps", str(artifact)])
        origin = run(
            [
                str(python),
                "-c",
                "import fictional_death_ledger; print(fictional_death_ledger.__file__)",
            ]
        ).strip()
        assert Path(origin).is_relative_to(prefix), origin
        doc = prefix / "share" / "doc" / "fictional-death-ledger"
        for name in ("README.md", "CHANGELOG.md", "DEVELOPMENT.md", "TESTING.md"):
            assert (doc / name).is_file(), name
        example = doc / "examples" / "novel.json"
        before = example.read_bytes()
        run([str(executable), "--help"])
        report = json.loads(run([str(executable), str(example), "--format", "json"]))
        assert report
        markdown = run([str(executable), str(example)])
        assert markdown.startswith("# ")
        through = json.loads(
            run([str(executable), str(example), "--through", "Chapter 1", "--format", "json"])
        )
        assert through["through"] == "Chapter 1"
        changed = json.loads(
            run(
                [
                    str(executable),
                    str(example),
                    "--between",
                    "Chapter 1",
                    "Chapter 8",
                    "--format",
                    "json",
                ]
            )
        )
        assert changed["mode"] == "changes"
        run([str(executable), str(example), "--between", "Chapter 1", "Chapter 8"])
        output = root / "report.md"
        run([str(executable), str(example), "--output", str(output)])
        saved = output.read_bytes()
        run([str(executable), str(example), "--output", str(output)], expected=2)
        assert output.read_bytes() == saved
        invalid = root / "bad.json"
        invalid.write_text('{"version":true}', encoding="utf-8")
        run([str(executable), str(invalid)], expected=2)
        assert example.read_bytes() == before
        print(
            json.dumps(
                {
                    "artifact": artifact.name,
                    "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                    "installed_origin": origin,
                    "checks": "help, docs, installed example, all report modes, output preservation, malformed input",
                    "status": "passed",
                }
            )
        )


if __name__ == "__main__":
    main()
