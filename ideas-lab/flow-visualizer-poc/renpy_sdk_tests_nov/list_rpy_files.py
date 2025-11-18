"""Utility to enumerate .rpy files inside a Ren'Py game's directory tree."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List, Optional


def collect_rpy_files(game_dir: Path, exclude_token: Optional[str] = "0x52") -> List[Path]:
    """
    Recursively collect every `.rpy` file inside `game_dir`.

    Args:
        game_dir: Path pointing to the `game/` directory of a Ren'Py project.

    Args:
        exclude_token: If provided, any directory whose name contains this
            (case-insensitive) substring is skipped entirely.

    Returns:
        Sorted list of resolved file paths for any `.rpy` scripts.

    Raises:
        FileNotFoundError: If `game_dir` does not exist.
        NotADirectoryError: If `game_dir` is not a directory.
    """
    if not game_dir.exists():
        raise FileNotFoundError(f"Game directory does not exist: {game_dir}")

    if not game_dir.is_dir():
        raise NotADirectoryError(f"Game directory is not a folder: {game_dir}")
    token = (exclude_token or "").lower()
    results: List[Path] = []

    for root, dirs, files in os.walk(game_dir):
        if token:
            dirs[:] = [d for d in dirs if token not in d.lower()]

        root_path = Path(root)
        for filename in files:
            if not filename.endswith(".rpy"):
                continue
            file_path = (root_path / filename).resolve()
            results.append(file_path)

    return sorted(results)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List every Ren'Py script (*.rpy) under the provided path."
    )
    parser.add_argument(
        "game_path",
        type=Path,
        help="Absolute path to the Ren'Py game's `game/` directory.",
    )
    parser.add_argument(
        "--exclude-token",
        type=str,
        default="0x52",
        help="Skip any subdirectory whose name contains this substring (default: 0x52).",
    )

    args = parser.parse_args()
    files = collect_rpy_files(args.game_path, exclude_token=args.exclude_token)

    if not files:
        print("No .rpy files found.")
        return

    print(f"Found {len(files)} .rpy files:\n")
    for path in files:
        print(path)


if __name__ == "__main__":
    main()

