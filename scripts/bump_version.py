from __future__ import annotations

import re
from pathlib import Path


def bump_patch(version: str) -> str:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version.strip())
    if not match:
        raise SystemExit(f"VERSION must be in X.Y.Z form, got: {version!r}")

    major, minor, patch = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return f"{major}.{minor}.{patch + 1}"


def main() -> None:
    version_path = Path("VERSION")
    current = version_path.read_text(encoding="utf-8").strip()
    updated = bump_patch(current)
    version_path.write_text(updated + "\n", encoding="utf-8")
    print(f"{current} -> {updated}")


if __name__ == "__main__":
    main()

