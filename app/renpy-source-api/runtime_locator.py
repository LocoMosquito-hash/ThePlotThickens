"""
Utilities for locating the Python interpreter bundled with a packaged Ren'Py game.

We often receive paths that point directly to the `game/` directory of a release
build. Every Ren'Py distribution already ships the matching Python runtime under
`lib/`, so we can bootstrap the SDK worker with the same interpreter the game
uses instead of forcing Ren'Py 8.4 for everything.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


WINDOWS_RUNTIME_FOLDERS: Sequence[str] = (
    "py3-windows-x86_64",
    "windows-x86_64",
    "py2-windows-x86_64",
    "py3-windows-i686",
    "py2-windows-i686",
    "windows-i686",
)

PYTHON_EXECUTABLE_CANDIDATES: Sequence[str] = (
    "python.exe",
    "pythonw.exe",
)


@dataclass(frozen=True)
class BundledPythonRuntime:
    """
    Metadata for a Python runtime discovered alongside a packaged Ren'Py game.
    """

    root_dir: Path
    """Root directory of the Ren'Py game (the folder that contains `game/`)."""

    lib_dir: Path
    """`root_dir / 'lib'`"""

    platform_dir: Path
    """Specific subdirectory under `lib` that contains the interpreter."""

    python_executable: Path
    """Absolute path to the interpreter binary (python.exe / pythonw.exe)."""

    descriptor: str
    """Folder name such as `py2-windows-x86_64` for logging purposes."""

    renpy_engine_dir: Optional[Path] = None
    """Absolute path to the bundled `renpy/` engine directory if it exists."""

    launcher_path: Optional[Path] = None
    """Path to the launcher script (<GameName>.py / renpy.py) if detected."""


def _resolve_game_root(path: Path) -> Path:
    """
    Ensure we are pointing at the Ren'Py game root, not `game/` itself.
    """

    path = path.resolve()
    if path.name.lower() == "game":
        return path.parent
    if (path / "game").is_dir():
        return path
    return path


def _iter_windows_runtime_dirs(lib_dir: Path) -> Iterable[Path]:
    for folder_name in WINDOWS_RUNTIME_FOLDERS:
        candidate = lib_dir / folder_name
        if candidate.is_dir():
            yield candidate


def _find_python_binary(platform_dir: Path) -> Optional[Path]:
    for filename in PYTHON_EXECUTABLE_CANDIDATES:
        candidate = platform_dir / filename
        if candidate.is_file():
            return candidate
    return None


def _find_launcher_script(root_dir: Path) -> Optional[Path]:
    python_files = list(root_dir.glob("*.py"))
    if not python_files:
        return None

    root_name = root_dir.name.lower().replace(" ", "")

    def _score(candidate: Path) -> Tuple[int, str]:
        stem = candidate.stem.lower()
        if stem == "renpy":
            return (0, candidate.name)
        if stem == root_name:
            return (1, candidate.name)
        if stem.startswith("renpy"):
            return (2, candidate.name)
        return (10, candidate.name)

    best = min(python_files, key=_score)
    return best


def locate_bundled_python(game_path: Path | str) -> Optional[BundledPythonRuntime]:
    """
    Locate the Python interpreter shipped with a packaged Ren'Py game.

    Args:
        game_path: Path to the `game/` directory or its parent.

    Returns:
        BundledPythonRuntime metadata if a Windows interpreter is found, otherwise None.
    """

    root_dir = _resolve_game_root(Path(game_path))
    lib_dir = root_dir / "lib"
    if not lib_dir.is_dir():
        return None

    launcher_path = _find_launcher_script(root_dir)

    for platform_dir in _iter_windows_runtime_dirs(lib_dir):
        python_binary = _find_python_binary(platform_dir)
        if python_binary is None:
            continue

        renpy_engine = root_dir / "renpy"
        return BundledPythonRuntime(
            root_dir=root_dir,
            lib_dir=lib_dir,
            platform_dir=platform_dir,
            python_executable=python_binary,
            descriptor=platform_dir.name,
            renpy_engine_dir=renpy_engine if renpy_engine.is_dir() else None,
            launcher_path=launcher_path,
        )

    return None


def locate_all_bundled_pythons(game_path: Path | str) -> List[BundledPythonRuntime]:
    """
    Return every Windows runtime discovered under the game's `lib/` directory.

    The list is ordered by preference (64-bit folders first).
    """

    root_dir = _resolve_game_root(Path(game_path))
    lib_dir = root_dir / "lib"
    runtimes: List[BundledPythonRuntime] = []
    if not lib_dir.is_dir():
        return runtimes

    launcher_path = _find_launcher_script(root_dir)

    for platform_dir in _iter_windows_runtime_dirs(lib_dir):
        python_binary = _find_python_binary(platform_dir)
        if python_binary is None:
            continue

        renpy_engine = root_dir / "renpy"
        runtimes.append(
            BundledPythonRuntime(
                root_dir=root_dir,
                lib_dir=lib_dir,
                platform_dir=platform_dir,
                python_executable=python_binary,
                descriptor=platform_dir.name,
                renpy_engine_dir=renpy_engine if renpy_engine.is_dir() else None,
                launcher_path=launcher_path,
            )
        )

    return runtimes


def _print_result(game_path: str) -> None:
    runtime = locate_bundled_python(game_path)
    if runtime is None:
        print(f"{game_path} -> no Windows runtime detected")
        return
    renpy_info = (
        f", renpy: {runtime.renpy_engine_dir}"
        if runtime.renpy_engine_dir is not None
        else ", renpy: <missing>"
    )
    launcher_info = (
        f", launcher: {runtime.launcher_path}"
        if runtime.launcher_path is not None
        else ", launcher: <missing>"
    )
    print(
        f"{game_path} -> {runtime.descriptor} (python: {runtime.python_executable}"
        f"{renpy_info}{launcher_info})"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Locate the Python interpreter shipped with a Ren'Py game.",
    )
    parser.add_argument(
        "game_paths",
        nargs="+",
        help="Path(s) to the 'game' directory or its parent.",
    )
    args = parser.parse_args()

    for input_path in args.game_paths:
        _print_result(input_path)

