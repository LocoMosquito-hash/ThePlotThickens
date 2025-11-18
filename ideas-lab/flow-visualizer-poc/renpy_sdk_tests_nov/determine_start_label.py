"""Determine the entry label of a Ren'Py project by running the SDK parser."""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path
from typing import Callable, Optional

# Default relative path to the unpacked Ren'Py 8.4.0 SDK copy.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SDK = PROJECT_ROOT / "app/renpy-source-api/renpy_sdk/renpy-8.4.0-sdk"

_STORE_LABEL_CALLBACK: Optional[Callable[[str], None]] = None


class StartLabelResolutionError(RuntimeError):
    """Raised when the SDK bootstrap finishes without producing a start label."""


def _load_launcher_module(renpy_base: Path):
    """
    Dynamically import the official `renpy.py` launcher so we can reuse its helpers.
    """
    launcher_path = renpy_base / "renpy.py"

    if not launcher_path.is_file():
        raise FileNotFoundError(f"Ren'Py launcher script missing: {launcher_path}")

    spec = importlib.util.spec_from_file_location("renpy_sdk_launcher", launcher_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load Ren'Py launcher from {launcher_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _flow_start_label_command() -> bool:
    """
    Command entry point invoked by Ren'Py after init to capture the start label.
    """
    import renpy.arguments  # type: ignore
    import renpy.config  # type: ignore

    parser = renpy.arguments.ArgumentParser(
        description="Dump the effective Ren'Py start label.",
        require_command=False,
    )
    parser.add_argument(
        "--default",
        default="start",
        help="Fallback label name when config.start_label is unset.",
    )
    args = parser.parse_args()

    start_label = getattr(renpy.config, "start_label", None)  # type: ignore[attr-defined]
    label = start_label or args.default

    if _STORE_LABEL_CALLBACK is not None:
        _STORE_LABEL_CALLBACK(label)

    return False


def _register_start_label_command(store_label: Callable[[str], None]) -> None:
    """
    Register a custom Ren'Py CLI command that captures `config.start_label`.
    """
    import renpy.arguments  # type: ignore

    global _STORE_LABEL_CALLBACK
    _STORE_LABEL_CALLBACK = store_label

    renpy.arguments.register_command(
        "flow_start_label",
        _flow_start_label_command,
        uses_display=False,
    )


def _resolve_project_base(path: Path) -> Path:
    """
    Accept either the project root or its `game/` subdirectory and normalize to the root.
    """
    path = path.resolve()

    if (path / "game").is_dir():
        return path

    if path.name.lower() == "game":
        parent = path.parent
        if (parent / "game").is_dir():
            return parent

    raise NotADirectoryError(
        "Provide the Ren'Py project directory (the folder that contains the `game/` subdirectory)."
    )


def determine_start_label(game_path: Path, sdk_path: Optional[Path] = None) -> str:
    """
    Bootstrap the Ren'Py SDK for `game_path` and return the effective entry label.
    """
    sdk_base = (sdk_path or DEFAULT_SDK).resolve()
    if not sdk_base.exists():
        raise FileNotFoundError(f"Ren'Py SDK path does not exist: {sdk_base}")

    project_base = _resolve_project_base(game_path)

    def platform_runtime_dir(base: Path) -> Optional[Path]:
        if sys.platform.startswith("win"):
            return base / "lib" / "py3-windows-x86_64"
        if sys.platform == "darwin":
            return base / "lib" / "py3-mac-universal"
        if sys.platform.startswith("linux"):
            return base / "lib" / "py3-linux-x86_64"
        return None

    sys_path_backup = list(sys.path)
    argv_backup = list(sys.argv)
    cwd_backup = Path.cwd()
    original_env_path = os.environ.get("PATH", "")

    python_stdlib = sdk_base / "lib" / "python3.12"
    python_site_packages = python_stdlib / "site-packages"

    sys.path.insert(0, str(sdk_base))
    if python_site_packages.exists():
        sys.path.insert(0, str(python_site_packages))
    if python_stdlib.exists():
        sys.path.insert(0, str(python_stdlib))

    runtime_dir = platform_runtime_dir(sdk_base)
    if runtime_dir and runtime_dir.exists():
        os.environ["PATH"] = f"{runtime_dir}{os.pathsep}{original_env_path}"

    os.chdir(sdk_base)

    launcher_module = _load_launcher_module(sdk_base)
    current_main = sys.modules[__name__]

    for attr in (
        "path_to_gamedir",
        "path_to_common",
        "path_to_saves",
        "path_to_logdir",
        "predefined_searchpath",
    ):
        if hasattr(launcher_module, attr):
            setattr(current_main, attr, getattr(launcher_module, attr))

    import renpy.bootstrap  # type: ignore
    import renpy  # type: ignore

    renpy.__main__ = launcher_module  # type: ignore[attr-defined]

    captured_label: Optional[str] = None

    def store_label(value: str) -> None:
        nonlocal captured_label
        captured_label = value

    _register_start_label_command(store_label)

    sys.argv = [
        str(sdk_base / "renpy.py"),
        str(project_base),
        "flow_start_label",
    ]

    try:
        try:
            renpy.bootstrap.bootstrap(str(sdk_base))
        except SystemExit as exc:
            if exc.code not in (0, None):
                raise
    finally:
        sys.path = sys_path_backup
        sys.argv = argv_backup
        os.chdir(cwd_backup)
        os.environ["PATH"] = original_env_path

    if captured_label is None:
        raise StartLabelResolutionError("SDK finished without reporting a start label.")

    return captured_label


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Determine which label Ren'Py uses as the entry point for a project.",
    )
    parser.add_argument(
        "game_path",
        type=Path,
        help="Path to the Ren'Py project directory (or its `game/` subdirectory).",
    )
    parser.add_argument(
        "--sdk-path",
        type=Path,
        default=DEFAULT_SDK,
        help="Path to the unpacked Ren'Py SDK to use (default: %(default)s).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the detected label (useful with GUI-only Python builds).",
    )

    args = parser.parse_args()
    label = determine_start_label(args.game_path, args.sdk_path)
    if args.output:
        args.output.write_text(f"{label}\n", encoding="utf-8")
    else:
        print(label)


if __name__ == "__main__":
    main()

