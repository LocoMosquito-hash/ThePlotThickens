"""Inspect a Ren'Py label node using the official SDK."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _load_flowviz_config(game_dir: Path) -> Tuple[List[str], List[str]]:
    """
    Read flowviz_config.json (if present) and return ignore/force entries.
    """
    config_path = game_dir / "flowviz_config.json"
    if not config_path.exists():
        return [], []

    try:
        with config_path.open("r", encoding="utf-8") as fh:
            config = json.load(fh)
    except Exception as exc:
        print(
            f"[INSPECT][CONFIG] Failed to parse {config_path}: {exc}",
            file=sys.stderr,
        )
        return [], []

    def _string_list(key: str) -> List[str]:
        entries = config.get(key, [])
        if not isinstance(entries, list):
            return []
        result: List[str] = []
        for entry in entries:
            if isinstance(entry, str):
                stripped = entry.strip()
                if stripped:
                    result.append(stripped)
        return result

    ignore_entries = _string_list("ignore_files")
    force_entries = _string_list("force_rpyc_files")

    if ignore_entries or force_entries:
        print(
            f"[INSPECT][CONFIG] Loaded flowviz_config.json from {config_path}",
            file=sys.stderr,
        )
        if ignore_entries:
            print(
                f"[INSPECT][CONFIG] Ignored files: {ignore_entries}",
                file=sys.stderr,
            )
        if force_entries:
            print(
                f"[INSPECT][CONFIG] Forced .rpyc files: {force_entries}",
                file=sys.stderr,
            )

    return ignore_entries, force_entries


def _dedupe_entries(entries: List[str]) -> List[str]:
    deduped: List[str] = []
    seen: set[str] = set()
    for entry in entries:
        stripped = entry.strip()
        if not stripped:
            continue
        if stripped in seen:
            continue
        seen.add(stripped)
        deduped.append(stripped)
    return deduped


def _next_available_suffix(path: Path, suffix: str) -> Path:
    candidate = path.with_suffix(path.suffix + suffix)
    counter = 1
    while candidate.exists():
        candidate = path.with_suffix(path.suffix + f"{suffix}{counter}")
        counter += 1
    return candidate


def _hide_source_files(game_dir: Path, entries: List[str]) -> List[Tuple[Path, Path]]:
    hidden: List[Tuple[Path, Path]] = []
    for entry in entries:
        clean = entry.strip()
        if not clean:
            continue
        target = Path(clean)
        if not target.is_absolute():
            target = game_dir / target
        if not target.exists():
            continue
        hidden_path = _next_available_suffix(target, ".flowignore")
        try:
            target.rename(hidden_path)
            hidden.append((target, hidden_path))
        except Exception as err:
            print(f"[INSPECT] Failed to hide {target}: {err}", file=sys.stderr)
    if hidden:
        print(f"[INSPECT] Temporarily hiding {len(hidden)} source files to force .rpyc usage.", file=sys.stderr)
    return hidden


def _restore_hidden_sources(hidden: List[Tuple[Path, Path]]) -> None:
    for original, temp in reversed(hidden):
        try:
            if original.exists():
                original.unlink()
            if temp.exists():
                temp.rename(original)
        except Exception as err:
            print(f"[INSPECT] Failed to restore {original} from {temp}: {err}", file=sys.stderr)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SDK = PROJECT_ROOT / "app/renpy-source-api/renpy_sdk/renpy-8.4.0-sdk"

_TARGET_LABEL: Optional[str] = None
_PROJECT_BASE: Optional[Path] = None
_CAPTURED_LABEL_DETAILS: Optional[str] = None
_MAX_STATEMENTS: int = 20
_HIDDEN_SOURCES: List[Tuple[Path, Path]] = []


class LabelInspectionError(RuntimeError):
    """Raised when the SDK cannot provide information for the requested label."""


def _load_launcher_module(renpy_base: Path):
    launcher_path = renpy_base / "renpy.py"

    if not launcher_path.is_file():
        raise FileNotFoundError(f"Ren'Py launcher script missing: {launcher_path}")

    spec = importlib.util.spec_from_file_location("renpy_sdk_launcher", launcher_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load Ren'Py launcher from {launcher_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _relativize(path: Optional[str]) -> Optional[str]:
    if not path:
        return None

    path_obj = Path(path)

    if not path_obj.is_absolute():
        if _PROJECT_BASE:
            path_obj = (_PROJECT_BASE / path_obj).resolve()
        else:
            path_obj = path_obj.resolve()
    else:
        path_obj = path_obj.resolve()
    if _PROJECT_BASE:
        try:
            return str(path_obj.relative_to(_PROJECT_BASE))
        except ValueError:
            pass
    return str(path_obj)


def _detect_sdk_from_executable() -> Optional[Path]:
    exe_path = Path(sys.executable).resolve()
    for parent in exe_path.parents:
        if (parent / "renpy.py").is_file():
            return parent
    return None


def _remove_other_sdk_paths(paths: List[str], target_sdk: Path) -> List[str]:
    cleaned: List[str] = []
    target_sdk = target_sdk.resolve()

    for entry in paths:
        try:
            resolved = Path(entry).resolve()
        except Exception:
            cleaned.append(entry)
            continue

        if resolved == target_sdk or target_sdk in resolved.parents:
            cleaned.append(entry)
            continue

        if "renpy_sdk" in resolved.parts and any(part.startswith("renpy-") for part in resolved.parts):
            # Skip other SDK versions.
            continue

        cleaned.append(entry)

    return cleaned


def _describe_ast_node(node: Any) -> Optional[Dict[str, Any]]:
    if node is None:
        return None

    description: Dict[str, Any] = {
        "node_type": type(node).__name__,
        "location": _format_location(node),
        "attrs": _collect_attrs(node, skip=["block", "next"]),
    }
    return description


def _summarize_if_branches(if_node: Any) -> List[Dict[str, Any]]:
    branches: List[Dict[str, Any]] = []
    entries = getattr(if_node, "entries", []) or []

    for condition, block in entries:
        block_statements = block or []
        branch_info: Dict[str, Any] = {
            "condition": _simple_value(condition),
            "statement_count": len(block_statements),
        }
        if block_statements:
            branch_info["first_statement"] = _describe_ast_node(block_statements[0])
            branch_info["tail_next"] = _describe_ast_node(getattr(block_statements[-1], "next", None))
        branches.append(branch_info)

    else_block = getattr(if_node, "else_", None)
    if else_block:
        block_statements = else_block or []
        branch_info = {
            "condition": "else",
            "statement_count": len(block_statements),
        }
        if block_statements:
            branch_info["first_statement"] = _describe_ast_node(block_statements[0])
            branch_info["tail_next"] = _describe_ast_node(getattr(block_statements[-1], "next", None))
        branches.append(branch_info)

    return branches


def _simple_value(value: Any, depth: int = 0) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    if depth >= 2:
        return repr(value)

    if isinstance(value, (list, tuple)):
        limited = [_simple_value(item, depth + 1) for item in value[:5]]
        if len(value) > 5:
            limited.append(f"... ({len(value) - 5} more)")
        return limited

    if isinstance(value, dict):
        result: Dict[str, Any] = {}
        for key in list(value.keys())[:5]:
            result[str(key)] = _simple_value(value[key], depth + 1)
        if len(value) > 5:
            result["__extra__"] = f"... ({len(value) - 5} more keys)"
        return result

    return repr(value)


def _collect_attrs(obj: Any, skip: Optional[List[str]] = None) -> Dict[str, Any]:
    attrs: Dict[str, Any] = {}
    ignored = set(skip or [])
    ignored.add("next")

    obj_dict = getattr(obj, "__dict__", None)

    if obj_dict:
        for key, value in obj_dict.items():
            if key.startswith("_") or key in ignored:
                continue
            attrs[key] = _simple_value(value)
        return attrs

    for key in dir(obj):
        if key.startswith("_") or key in ignored:
            continue
        try:
            value = getattr(obj, key)
        except Exception:
            continue
        if callable(value):
            continue
        attrs[key] = _simple_value(value)

    return attrs


def _format_location(obj: Any) -> Optional[str]:
    filename = getattr(obj, "filename", None)
    linenumber = getattr(obj, "linenumber", None)

    loc = getattr(obj, "loc", None)
    if not filename and loc is not None:
        filename = getattr(loc, "filename", None)
        linenumber = getattr(loc, "linenumber", None)

    if not filename:
        return None

    rel = _relativize(filename)
    if linenumber:
        return f"{rel}:{linenumber}"
    return rel


def _summarize_statement(stmt: Any, index: int) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "index": index,
        "type": type(stmt).__name__,
        "location": _format_location(stmt),
        "attrs": _collect_attrs(stmt, skip=["block"]),
    }

    block = getattr(stmt, "block", None)
    if block is not None:
        child_stmts = getattr(block, "statements", [])
        summary["nested_statement_count"] = len(child_stmts)

    summary["next_pointer"] = _describe_ast_node(getattr(stmt, "next", None))

    import renpy.ast  # type: ignore

    if isinstance(stmt, renpy.ast.If):
        summary["branches"] = _summarize_if_branches(stmt)

    return summary


def _gather_label_info(label_name: str, max_statements: int) -> Dict[str, Any]:
    import renpy.game  # type: ignore
    import renpy.config  # type: ignore

    script = renpy.game.script

    try:
        node = script.lookup(label_name)
    except Exception as exc:  # pragma: no cover - Ren'Py specific error types
        return {"label": label_name, "error": str(exc)}

    info: Dict[str, Any] = {
        "label": label_name,
        "node_type": type(node).__name__,
        "location": _format_location(node),
        "attributes": _collect_attrs(node, skip=["block", "name"]),
        "gamedir": str(renpy.config.gamedir),
    }

    block = getattr(node, "block", None)
    statements: List[Any] = []

    if isinstance(block, list):
        statements = block
    elif block is not None:
        statements = getattr(block, "statements", [])

    if statements:
        info["block_statement_count"] = len(statements)

        limit = max_statements if max_statements > 0 else len(statements)
        previews = [
            _summarize_statement(stmt, idx) for idx, stmt in enumerate(statements[:limit])
        ]
        if max_statements > 0 and len(statements) > max_statements:
            previews.append({"note": f"... truncated {len(statements) - max_statements} more statements"})
        info["block_statements"] = previews
    else:
        info["block_statement_count"] = 0
        info["block_statements"] = []

    info["next_pointer"] = _describe_ast_node(getattr(node, "next", None))

    return info


def _label_dump_command() -> bool:
    import renpy.arguments  # type: ignore

    parser = renpy.arguments.ArgumentParser(
        description="Inspect a Ren'Py label node.",
        require_command=False,
    )
    parser.add_argument(
        "--default",
        default="start",
        help="Fallback label name when none is provided.",
    )
    parser.add_argument(
        "--max-statements",
        type=int,
        default=_MAX_STATEMENTS,
        help="Maximum statements to show (<=0 means no limit).",
    )
    args = parser.parse_args()

    label_name = _TARGET_LABEL or args.default
    info = _gather_label_info(label_name, args.max_statements)

    global _CAPTURED_LABEL_DETAILS
    _CAPTURED_LABEL_DETAILS = json.dumps(info, indent=2, ensure_ascii=False)

    return False


def _register_label_command() -> None:
    import renpy.arguments  # type: ignore

    renpy.arguments.register_command(
        "flow_inspect_label",
        _label_dump_command,
        uses_display=False,
    )


def _resolve_project_base(path: Path) -> Path:
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


def inspect_label(
    game_path: Path,
    label_name: str,
    sdk_path: Optional[Path] = None,
    *,
    max_statements: int = 20,
    ignore_sources: Optional[List[str]] = None,
) -> str:
    if sdk_path:
        sdk_base = sdk_path.resolve()
    else:
        detected = _detect_sdk_from_executable()
        sdk_base = (detected or DEFAULT_SDK).resolve()

    print(f"[INSPECT] Using SDK base: {sdk_base}", file=sys.stderr)

    if not sdk_base.exists():
        raise FileNotFoundError(f"Ren'Py SDK path does not exist: {sdk_base}")

    project_base = _resolve_project_base(game_path)
    print(f"[INSPECT] Project base: {project_base}", file=sys.stderr)
    game_dir = project_base / "game"

    py_major = sys.version_info.major
    py_minor = sys.version_info.minor
    python_stdlib = sdk_base / "lib" / f"python{py_major}.{py_minor}"
    print(f"[INSPECT] Python stdlib: {python_stdlib}", file=sys.stderr)
    python_site_packages = python_stdlib / "site-packages"

    sys_path_backup = list(sys.path)
    argv_backup = list(sys.argv)
    cwd_backup = Path.cwd()
    original_env_path = os.environ.get("PATH", "")

    sys.path = _remove_other_sdk_paths(sys.path, sdk_base)
    sys.path.insert(0, str(sdk_base))
    if python_site_packages.exists():
        sys.path.insert(0, str(python_site_packages))
    if python_stdlib.exists():
        sys.path.insert(0, str(python_stdlib))

    def platform_runtime_dir(base: Path) -> Optional[Path]:
        if sys.platform.startswith("win"):
            return base / "lib" / "py3-windows-x86_64"
        if sys.platform == "darwin":
            return base / "lib" / "py3-mac-universal"
        if sys.platform.startswith("linux"):
            return base / "lib" / "py3-linux-x86_64"
        return None

    runtime_dir = platform_runtime_dir(sdk_base)
    if runtime_dir and runtime_dir.exists():
        os.environ["PATH"] = f"{runtime_dir}{os.pathsep}{original_env_path}"

    os.chdir(sdk_base)

    for module_name in list(sys.modules):
        if module_name.startswith("renpy"):
            del sys.modules[module_name]

    launcher_module = _load_launcher_module(sdk_base)
    print(f"[INSPECT] Using launcher: {sdk_base / 'renpy.py'}", file=sys.stderr)
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

    if os.environ.get("INSPECT_LABEL_DEBUG"):
        print(f"[INSPECT] sys.path before import: {sys.path}", file=sys.stderr)

    import renpy.bootstrap  # type: ignore
    import renpy  # type: ignore

    renpy.__main__ = launcher_module  # type: ignore[attr-defined]

    global _TARGET_LABEL, _PROJECT_BASE, _MAX_STATEMENTS
    _TARGET_LABEL = label_name
    _PROJECT_BASE = project_base
    _MAX_STATEMENTS = max_statements

    _register_label_command()

    sys.argv = [
        str(sdk_base / "renpy.py"),
        str(project_base),
        "flow_inspect_label",
        f"--max-statements={max_statements}",
    ]

    config_ignore, config_force = _load_flowviz_config(game_dir)
    combined_ignore = _dedupe_entries(list(ignore_sources or []) + config_ignore)
    forced_sources = _dedupe_entries(config_force)

    hidden_sources: List[Tuple[Path, Path]] = []
    if combined_ignore:
        hidden_sources.extend(_hide_source_files(game_dir, combined_ignore))
    if forced_sources:
        hidden_sources.extend(_hide_source_files(game_dir, forced_sources))

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
        _restore_hidden_sources(hidden_sources)

    if _CAPTURED_LABEL_DETAILS is None:
        raise LabelInspectionError("SDK finished without returning label information.")

    return _CAPTURED_LABEL_DETAILS


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dump structured information for a Ren'Py label using the Ren'Py SDK."
    )
    parser.add_argument(
        "game_path",
        type=Path,
        help="Path to the Ren'Py project directory (or its `game/` subdirectory).",
    )
    parser.add_argument(
        "label",
        type=str,
        help="Name of the label to inspect.",
    )
    parser.add_argument(
        "--sdk-path",
        type=Path,
        default=None,
        help="Optional path to a specific Ren'Py SDK. Defaults to the SDK bundled with this script, or autodetects from the running interpreter.",
    )
    parser.add_argument(
        "--max-statements",
        type=int,
        default=20,
        help="Maximum statements to show (<=0 means all statements).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional file to write the inspection JSON to (useful for GUI-only Python builds).",
    )
    parser.add_argument(
        "--ignore-source",
        action="append",
        default=[],
        help="Relative path (from game/) of a .rpy source file to hide so its compiled .rpyc is used instead. Repeat to add multiple entries.",
    )

    args = parser.parse_args()
    details = inspect_label(
        args.game_path,
        args.label,
        args.sdk_path,
        max_statements=args.max_statements,
        ignore_sources=args.ignore_source,
    )

    if args.output:
        args.output.write_text(details + "\n", encoding="utf-8")
    else:
        print(details)


if __name__ == "__main__":
    main()

