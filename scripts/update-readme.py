"""Generate the README's latest-version block from CHANGELOG.md."""
import argparse
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- latest-version:start -->"
END = "<!-- latest-version:end -->"


def render(changelog, readme):
    versions = list(re.finditer(
        r"^## \[(\d+\.\d+\.\d+)\] - (Unreleased|\d{4}-\d{2}-\d{2})$",
        changelog, re.MULTILINE))
    if not versions:
        raise ValueError("CHANGELOG.md needs a version heading: ## [X.Y.Z] - Unreleased or YYYY-MM-DD")
    latest = versions[0]
    notes = changelog[latest.end():versions[1].start() if len(versions) > 1 else len(changelog)].strip()
    if not notes:
        raise ValueError("The latest changelog version has no release notes")
    block = (f"{START}\n## Latest version: {latest[1]} ({latest[2]})\n\n"
             f"{notes}\n\n[Full changelog](CHANGELOG.md)\n{END}")
    if START not in readme and END not in readme:
        heading, separator, rest = readme.partition("\n")
        if not separator or not heading.startswith("# "):
            raise ValueError("README.md needs a top-level title")
        return f"{heading}\n\n{block}\n\n{rest.lstrip()}"
    if readme.count(START) != 1 or readme.count(END) != 1 or readme.index(START) > readme.index(END):
        raise ValueError("README.md has malformed latest-version markers")
    return readme[:readme.index(START)] + block + readme[readme.index(END) + len(END):]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the README is out of date; write nothing")
    args = parser.parse_args()
    try:
        path = ROOT / "README.md"
        current = path.read_text(encoding="utf-8-sig")
        expected = render((ROOT / "CHANGELOG.md").read_text(encoding="utf-8-sig"), current)
        if current != expected:
            if args.check:
                parser.exit(1, "README version notes are stale. Run: python scripts/update-readme.py\n")
            path.write_text(expected, encoding="utf-8", newline="\n")
            print("Updated README version notes from CHANGELOG.md")
        else:
            print("README version notes match CHANGELOG.md")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Version notes failed: {error}\n")
