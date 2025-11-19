#!/usr/bin/env python3
"""
Worker script executed by the official Ren'Py SDK python interpreter.

This scripts boots the Ren'Py runtime, walks the AST, and emits a JSON payload
with the flow graph structure that mirrors the legacy regex-based output.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
import textwrap
import traceback
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT_DIR = Path(__file__).parent
SDK_DIR = ROOT_DIR / "renpy_sdk" / "renpy-8.4.0-sdk"
PYTHON_STDLIB = SDK_DIR / "lib" / "python3.12"
SITE_PACKAGES = PYTHON_STDLIB / "site-packages"
STATE: Optional["_ExtractionState"] = None
DEBUG_ENABLED = os.environ.get("SDK_FLOW_DEBUG") == "1"
FLOW_CONFIG: Dict[str, Any] = {}
IGNORED_PATHS: Set[Path] = set()
FORCE_RPYC_PATHS: Set[Path] = set()
PROJECT_ROOT: Optional[Path] = None
GAME_DIR: Optional[Path] = None
_HIDDEN_SOURCE_ORIGINALS: Set[Path] = set()


def _prepare_environment() -> None:
    sys.path.insert(0, str(SDK_DIR))
    if PYTHON_STDLIB.exists():
        sys.path.insert(0, str(PYTHON_STDLIB))
    if SITE_PACKAGES.exists():
        sys.path.insert(0, str(SITE_PACKAGES))


def _load_launcher_module():
    launcher_path = SDK_DIR / "renpy.py"
    spec = importlib.util.spec_from_file_location("renpy_sdk_launcher", launcher_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Ren'Py launcher module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _ExtractionState:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None


class ASTFlowExtractor:
    def __init__(self, project_root: Path):
        import renpy  # type: ignore

        self.project_root = project_root
        self.script = renpy.game.script  # type: ignore[attr-defined]
        self._excluded_roots = self._build_exclusion_roots()

    def build_payload(self) -> Dict[str, Any]:
        labels: List[Dict[str, Any]] = []

        if DEBUG_ENABLED:
            import sys

            try:
                namemap_size = len(self.script.namemap)  # type: ignore[attr-defined]
            except Exception:
                namemap_size = -1
            sample = []
            string_keys = 0
            try:
                for idx, (key, value) in enumerate(self.script.namemap.items()):  # type: ignore[attr-defined]
                    if isinstance(key, str):
                        string_keys += 1
                    if idx >= 5:
                        break
                    sample.append((repr(key), type(key).__name__, type(value).__name__))
            except Exception:
                sample = []
            try:
                if string_keys == 0:
                    string_keys = sum(1 for key in self.script.namemap.keys() if isinstance(key, str))  # type: ignore[attr-defined]
            except Exception:
                string_keys = -1
            print(
                f"[SDK_WORKER] namemap size: {namemap_size} string_keys: {string_keys} sample: {sample}",
                file=sys.stderr,
            )

        for node in self.script.namemap.values():  # type: ignore[attr-defined]
            if node is None:
                continue
            if self._is_excluded_source(getattr(node, "filename", None)):
                continue
            if self._is_label_node(node):
                analyzer = LabelAnalyzer(node.name, node, self.project_root)
                labels.append(analyzer.analyze())

        screens = self._collect_screens()
        return {"labels": labels, "screens": screens}

    def _is_label_node(self, node: Any) -> bool:
        import renpy.ast  # type: ignore

        return isinstance(node, renpy.ast.Label)

    def _collect_screens(self) -> List[Dict[str, Any]]:
        try:
            import renpy.display.screen  # type: ignore
        except Exception:
            return []

        payload: List[Dict[str, Any]] = []
        for screen_name, screen in renpy.display.screen.screens.items():  # type: ignore[attr-defined]
            if not hasattr(screen, "ast"):
                continue
            filename = getattr(screen.ast, "filename", "")
            if self._is_excluded_source(filename) or not self._is_project_screen(screen_name, filename):
                continue
            payload.append(
                {
                    "screen_name": screen_name,
                    "file_path": self._normalize_source(getattr(screen.ast, "filename", "")),
                    "line_number": getattr(screen.ast, "linenumber", 0),
                    "elements": [],
                }
            )
        return payload

    @staticmethod
    def _normalize_source(filename: Optional[str]) -> str:
        if not filename:
            return ""
        path = Path(filename)
        try:
            return str(path.resolve())
        except OSError:
            return filename

    def _build_exclusion_roots(self) -> List[Path]:
        roots: List[Path] = []
        candidates = [
            self.project_root / "renpy",
            self.project_root / "game" / "0x52-URM",
            self.project_root / "0x52-URM",
        ]
        for candidate in candidates:
            if candidate.exists():
                try:
                    roots.append(candidate.resolve())
                except OSError:
                    roots.append(candidate)
        return roots

    def _is_excluded_source(self, filename: Optional[str]) -> bool:
        if not filename:
            return False
        path = Path(filename)
        try:
            if not path.is_absolute():
                path = (self.project_root / path).resolve()
            else:
                path = path.resolve()
        except OSError:
            return False

        if _is_ignored_absolute(path):
            return True

        for root in self._excluded_roots:
            try:
                path.relative_to(root)
                return True
            except ValueError:
                continue

        lower_parts = [part.lower() for part in path.parts]
        if "0x52-urm" in lower_parts:
            return True
        return False

    def _is_project_screen(self, screen_name: str, filename: Optional[str]) -> bool:
        if not filename:
            return False
        path = Path(filename)
        try:
            if not path.is_absolute():
                path = (self.project_root / path).resolve()
            else:
                path = path.resolve()
        except OSError:
            return False

        # Only allow screens under game/
        try:
            path.relative_to(self.project_root / "game")
        except ValueError:
            return False

        # Previously we skipped stock UI helpers by name (screen_, director_, load_, save_),
        # but that also hid project-specific narrative screens that follow those naming
        # conventions. Keep the code around for quick reactivation if needed.
        # if screen_name.startswith("screen_") or screen_name.startswith("director_") \
        #         or screen_name.startswith("load_") or screen_name.startswith("save_"):
        #     return False

        return True


class LabelAnalyzer:
    def __init__(self, label_name: str, label_ast: Any, project_root: Path):
        self.label_name = label_name
        self.label_ast = label_ast
        self.menu_counter = 0
        self.project_root = project_root

        self.outgoing_flows: List[Dict[str, Any]] = []
        self.menu_nodes: List[Dict[str, Any]] = []
        self.has_dialogue = False
        self._visited_statements: Set[int] = set()

    def analyze(self) -> Dict[str, Any]:
        try:
            block = getattr(self.label_ast, "block", None)
            if block:
                self._walk_block(block, current_choice=None, nesting_level=0, active_condition=None)
            self._follow_pointer(
                getattr(self.label_ast, "next", None),
                current_choice=None,
                nesting_level=0,
                active_condition=None,
            )

            return {
                "name": self.label_name,
                "file_path": self._normalize_filename(getattr(self.label_ast, "filename", "")),
                "line_number": getattr(self.label_ast, "linenumber", 0),
                "has_dialogue": self.has_dialogue,
                "is_dead_end": len(self.outgoing_flows) == 0,
                "flow_complexity": len(self.outgoing_flows),
                "screen_calls": [],
                "outgoing_flows": self.outgoing_flows,
                "menu_nodes": self.menu_nodes,
            }
        except RecursionError as exc:
            context = self._format_label_context()
            raise RecursionError(f"Recursion while analyzing label '{self.label_name}' ({context})") from exc
        except Exception as exc:
            context = self._format_label_context()
            raise RuntimeError(
                f"Failed while analyzing label '{self.label_name}' ({context}): {exc}"
            ) from exc

    def _walk_block(
        self,
        statements: Any,
        current_choice: Optional[Dict[str, Any]],
        nesting_level: int,
        active_condition: Optional[str],
    ) -> None:
        iterable: List[Any]
        if hasattr(statements, "statements"):
            iterable = getattr(statements, "statements") or []
        else:
            iterable = statements or []

        for stmt in iterable:
            continue_scan = self._visit_statement(stmt, current_choice, nesting_level, active_condition)
            if not continue_scan:
                break
            next_stmt = getattr(stmt, "next", None)
            if next_stmt:
                self._follow_pointer(next_stmt, current_choice, nesting_level, active_condition)

    def _visit_statement(
        self,
        stmt: Any,
        current_choice: Optional[Dict[str, Any]],
        nesting_level: int,
        active_condition: Optional[str],
    ) -> bool:
        import renpy.ast  # type: ignore

        stmt_id = id(stmt)
        if stmt_id in self._visited_statements:
            return True
        self._visited_statements.add(stmt_id)

        if isinstance(stmt, renpy.ast.Say):
            self.has_dialogue = True
        elif isinstance(stmt, renpy.ast.Jump):
            self._record_flow(stmt, flow_type="jump", context="label_block", condition=active_condition)
        elif isinstance(stmt, renpy.ast.Call):
            flow_type = "call_expression" if getattr(stmt, "expression", False) else "call"
            self._record_flow(stmt, flow_type=flow_type, context="label_block", condition=active_condition)
        elif isinstance(stmt, renpy.ast.Return):
            self.outgoing_flows.append(
                {
                    "source_label": self.label_name,
                    "target_label": "<return>",
                    "flow_type": "return",
                    "file_path": self._normalize_filename(getattr(stmt, "filename", "")),
                    "line_number": getattr(stmt, "linenumber", 0),
                    "context": "label_block",
                    "condition": active_condition,
                }
            )
        elif isinstance(stmt, renpy.ast.Menu):
            self._process_menu(stmt, current_choice, nesting_level)
        elif isinstance(stmt, renpy.ast.If):
            for condition_expr, block in stmt.entries:
                if not block:
                    continue
                cond_label = self._stringify_condition(condition_expr)
                combined = self._combine_conditions(active_condition, cond_label)
                self._walk_block(block, current_choice, nesting_level, combined)
            else_block = getattr(stmt, "else_", None)
            if else_block:
                combined = self._combine_conditions(active_condition, "else")
                self._walk_block(else_block, current_choice, nesting_level, combined)
        elif isinstance(stmt, renpy.ast.Label):
            if getattr(stmt, "name", None) != self.label_name:
                self._record_fallthrough_transition(stmt, active_condition)
                return False
            return True
        elif getattr(stmt, "block", None):
            self._walk_block(stmt.block, current_choice, nesting_level, active_condition)

        return True

    def _record_flow(self, stmt: Any, flow_type: str, context: str, condition: Optional[str]) -> None:
        target = getattr(stmt, "target", None)
        if target is None and hasattr(stmt, "label"):
            target = getattr(stmt, "label")

        self.outgoing_flows.append(
            {
                "source_label": self.label_name,
                "target_label": target or "",
                "flow_type": flow_type
                if not getattr(stmt, "expression", False)
                else f"{flow_type}_expression",
                "file_path": self._normalize_filename(getattr(stmt, "filename", "")),
                "line_number": getattr(stmt, "linenumber", 0),
                "context": context,
                "condition": condition,
            }
        )

    def _follow_pointer(
        self,
        stmt: Optional[Any],
        current_choice: Optional[Dict[str, Any]],
        nesting_level: int,
        active_condition: Optional[str],
    ) -> None:
        import renpy.ast  # type: ignore

        while stmt is not None:
            if id(stmt) in self._visited_statements:
                break
            if isinstance(stmt, renpy.ast.Label):
                if getattr(stmt, "name", None) != self.label_name:
                    self._record_fallthrough_transition(stmt, active_condition)
                break
            self._visit_statement(stmt, current_choice, nesting_level, active_condition)
            stmt = getattr(stmt, "next", None)

    @staticmethod
    def _stringify_condition(condition: Any) -> str:
        try:
            text = getattr(condition, "text", None)
            if text is not None:
                return str(text)
        except Exception:
            pass
        if isinstance(condition, bool):
            return "True" if condition else "False"
        return str(condition)

    @staticmethod
    def _combine_conditions(parent: Optional[str], child: Optional[str]) -> Optional[str]:
        if parent and child:
            return f"({parent}) and ({child})"
        return child or parent

    def _record_fallthrough_transition(self, target_label_ast: Any, condition: Optional[str]) -> None:
        target_name = getattr(target_label_ast, "name", "")
        self.outgoing_flows.append(
            {
                "source_label": self.label_name,
                "target_label": target_name or "",
                "flow_type": "fallthrough",
                "file_path": self._normalize_filename(getattr(target_label_ast, "filename", "")),
                "line_number": getattr(target_label_ast, "linenumber", 0),
                "context": "implicit_follow",
                "condition": condition,
            }
        )

    def _process_menu(
        self,
        menu_stmt: Any,
        parent_choice: Optional[Dict[str, Any]],
        nesting_level: int,
    ) -> None:
        menu_payload = {
            "node_id": f"{self.label_name}_menu_{self.menu_counter}",
            "name": f"Menu {self.menu_counter + 1}",
            "parent_label": self.label_name,
            "menu_index": self.menu_counter,
            "file_path": self._normalize_filename(getattr(menu_stmt, "filename", "")),
            "line_number": getattr(menu_stmt, "linenumber", 0),
            "prompt": None,
            "is_nested": parent_choice is not None,
            "nesting_level": nesting_level,
            "choices": [],
        }
        self.menu_counter += 1

        for idx, (label, condition, block) in enumerate(menu_stmt.items):
            if label is None:
                continue

            choice_payload = {
                "text": label,
                "condition": None if condition == "True" else condition,
                "file_path": menu_payload["file_path"],
                "line_number": menu_payload["line_number"],
                "choice_index": idx,
                "destination": None,
                "all_destinations": [],
                "action_type": None,
                "leads_to_label": False,
                "leads_to_return": False,
                "nested_labels": [],
                "nested_menus": [],
            }
            self._analyze_choice_block(choice_payload, block)
            menu_payload["choices"].append(choice_payload)

        if parent_choice is not None:
            parent_choice["nested_menus"].append(menu_payload)
        else:
            self.menu_nodes.append(menu_payload)

    def _analyze_choice_block(self, choice: Dict[str, Any], block: Optional[List[Any]]) -> None:
        if not block:
            return

        import renpy.ast  # type: ignore

        for stmt in block:
            if isinstance(stmt, renpy.ast.Jump):
                target = getattr(stmt, "target", "")
                if target:
                    choice["all_destinations"].append(target)
                    if choice["destination"] is None:
                        choice["destination"] = target
                    choice["action_type"] = "jump"
                    choice["leads_to_label"] = True
            elif isinstance(stmt, renpy.ast.Call):
                target = getattr(stmt, "label", "")
                if target:
                    choice["all_destinations"].append(target)
                    if choice["destination"] is None:
                        choice["destination"] = target
                    choice["action_type"] = "call"
                    choice["leads_to_label"] = True
            elif isinstance(stmt, renpy.ast.Return):
                choice["all_destinations"].append("<return>")
                choice["destination"] = choice["destination"] or "<return>"
                choice["action_type"] = "return"
                choice["leads_to_return"] = True
            elif isinstance(stmt, renpy.ast.Label):
                choice["nested_labels"].append(getattr(stmt, "name", ""))
            elif isinstance(stmt, renpy.ast.Menu):
                self._process_menu(stmt, choice, nesting_level=1)
            elif isinstance(stmt, renpy.ast.If):
                for _, block in stmt.entries:
                    if block:
                        self._analyze_choice_block(choice, block)
                else_block = getattr(stmt, "else_", None)
                if else_block:
                    self._analyze_choice_block(choice, else_block)

            if hasattr(stmt, "block") and isinstance(stmt.block, list):
                self._analyze_choice_block(choice, stmt.block)

        if not choice["action_type"] and choice["destination"]:
            choice["action_type"] = "jump"

    def _normalize_filename(self, filename: Optional[str]) -> str:
        if not filename:
            return ""
        path = Path(filename)
        try:
            if not path.is_absolute():
                candidate = (self.project_root / path).resolve()
            else:
                candidate = path.resolve()
            return str(candidate)
        except OSError:
            return str(path)

    def _format_label_context(self) -> str:
        file_path = self._normalize_filename(getattr(self.label_ast, "filename", ""))
        line_number = getattr(self.label_ast, "linenumber", 0)
        if file_path:
            return f"{file_path}:{line_number}"
        return f"line {line_number}"


def _sdk_flow_command() -> bool:
    import renpy.arguments  # type: ignore

    if STATE is None:
        return False

    parser = renpy.arguments.ArgumentParser(require_command=False)  # type: ignore
    parser.parse_args()
    try:
        extractor = ASTFlowExtractor(STATE.project_root)
        STATE.result = extractor.build_payload()
    except Exception:
        error_text = traceback.format_exc()
        STATE.error = error_text
        if DEBUG_ENABLED:
            print(f"[SDK_WORKER] Flow extraction failed:\n{error_text}", file=sys.stderr)
    return False


def main() -> None:
    if len(sys.argv) < 2:
        print("{}", end="")
        return

    current_limit = sys.getrecursionlimit()
    if current_limit < 10000:
        sys.setrecursionlimit(10000)

    project_root = Path(sys.argv[1]).resolve()
    _load_flowviz_config(project_root)
    hidden_force = _temporarily_hide_force_rpyc_files()
    hidden_files = _temporarily_hide_ignored_files()
    sanitized_backups = _swap_in_sanitized_scripts(project_root)
    _prepare_environment()

    import renpy  # type: ignore
    import renpy.bootstrap  # type: ignore
    import renpy.arguments  # type: ignore
    import renpy.config as renpy_config  # type: ignore

    try:
        import codecs

        # Allow UTF-8 with BOM and other utf-8 variants transparently.
        renpy_config.script_encoding = "utf-8-sig"  # type: ignore[attr-defined]
    except Exception:
        pass

    search_dir = GAME_DIR if GAME_DIR is not None else project_root / "game"
    renpy_config.searchpath = [str(search_dir)]  # type: ignore[attr-defined]

    launcher_module = _load_launcher_module()
    renpy.__main__ = launcher_module  # type: ignore[attr-defined]
    main_module = sys.modules.get("__main__")
    if main_module:
        for attr in (
            "path_to_gamedir",
            "path_to_common",
            "path_to_saves",
            "path_to_logdir",
            "predefined_searchpath",
        ):
            if hasattr(launcher_module, attr):
                setattr(main_module, attr, getattr(launcher_module, attr))

    global STATE
    STATE = _ExtractionState(project_root)
    renpy.arguments.register_command("sdk_flow_worker", _sdk_flow_command, uses_display=False)  # type: ignore

    sys.argv = [
        str(SDK_DIR / "renpy.py"),
        str(project_root),
        "sdk_flow_worker",
    ]

    try:
        try:
            renpy.bootstrap.bootstrap(str(SDK_DIR))  # type: ignore
        except SystemExit as exc:  # pragma: no cover
            if exc.code not in (0, None):
                raise
    finally:
        _restore_sanitized_scripts(sanitized_backups)
        _restore_hidden_files(hidden_files)
        _restore_hidden_files(hidden_force)

    if STATE.error:
        raise RuntimeError(STATE.error)

    print(json.dumps(STATE.result or {}), flush=True)

def _swap_in_sanitized_scripts(project_root: Path) -> List[Tuple[Path, Path]]:
    backups: List[Tuple[Path, Path]] = []
    game_dir = project_root / "game"
    if not game_dir.exists():
        return backups

    for script_path in game_dir.rglob("*.rpy"):
        if _is_ignored_absolute(script_path) or _is_force_rpyc_absolute(script_path):
            continue
        try:
            text = script_path.read_text(encoding="utf-8-sig")
        except Exception:
            continue
        if not text.startswith((" ", "\t")):
            continue

        sanitized_text = textwrap.dedent(text)
        backup_path = script_path.with_suffix(script_path.suffix + ".sdkbak")
        suffix_index = 1
        while backup_path.exists():
            backup_path = script_path.with_suffix(script_path.suffix + f".sdkbak{suffix_index}")
            suffix_index += 1

        try:
            script_path.rename(backup_path)
            script_path.write_text(sanitized_text, encoding="utf-8")
            backups.append((script_path, backup_path))
        except Exception:
            if backup_path.exists():
                backup_path.rename(script_path)

    if backups and DEBUG_ENABLED:
        print(f"[SDK_WORKER] Sanitized {len(backups)} script files in-place for analysis.", file=sys.stderr)

    return backups


def _restore_sanitized_scripts(backups: List[Tuple[Path, Path]]) -> None:
    for original, backup in reversed(backups):
        try:
            if original.exists():
                original.unlink()
            if backup.exists():
                backup.rename(original)
        except Exception:
            continue


def _temporarily_hide_ignored_files() -> List[Tuple[Path, Path]]:
    hidden: List[Tuple[Path, Path]] = []
    for ignored in IGNORED_PATHS:
        if not ignored.exists():
            continue
        if not _is_within_game_dir(ignored):
            continue
        hidden_path = _next_available_suffix(ignored, ".flowignore")
        try:
            ignored.rename(hidden_path)
            _HIDDEN_SOURCE_ORIGINALS.add(ignored)
            hidden.append((ignored, hidden_path))
        except Exception:
            continue
    if hidden and DEBUG_ENABLED:
        print(f"[SDK_WORKER] Temporarily hiding {len(hidden)} ignored files.", file=sys.stderr)
    return hidden


def _restore_hidden_files(hidden: List[Tuple[Path, Path]]) -> None:
    for original, temp in reversed(hidden):
        try:
            if original.exists():
                original.unlink()
            if temp.exists():
                temp.rename(original)
            _HIDDEN_SOURCE_ORIGINALS.discard(original)
        except Exception:
            continue


def _temporarily_hide_force_rpyc_files() -> List[Tuple[Path, Path]]:
    hidden: List[Tuple[Path, Path]] = []
    for target in FORCE_RPYC_PATHS:
        if not target.exists():
            continue
        if target in _HIDDEN_SOURCE_ORIGINALS:
            continue
        if not _is_within_game_dir(target):
            continue
        if target.suffix.lower().endswith(".rpy"):
            compiled = target.with_suffix(target.suffix + "c")
            if not compiled.exists():
                continue
        hidden_path = _next_available_suffix(target, ".flowignore")
        try:
            target.rename(hidden_path)
            _HIDDEN_SOURCE_ORIGINALS.add(target)
            hidden.append((target, hidden_path))
        except Exception:
            continue
    if hidden and DEBUG_ENABLED:
        print(f"[SDK_WORKER] Forcing .rpyc usage for {len(hidden)} files.", file=sys.stderr)
    return hidden


def _load_flowviz_config(project_root: Path) -> None:
    global FLOW_CONFIG, IGNORED_PATHS, FORCE_RPYC_PATHS, GAME_DIR, PROJECT_ROOT
    PROJECT_ROOT = project_root
    game_dir = (project_root / "game").resolve()
    GAME_DIR = game_dir
    config_path = game_dir / "flowviz_config.json"
    FLOW_CONFIG = {}
    IGNORED_PATHS = set()
    FORCE_RPYC_PATHS = set()

    if not config_path.exists():
        if DEBUG_ENABLED:
            print(f"[SDK_WORKER] No flowviz_config.json found at {config_path}", file=sys.stderr)
        return

    try:
        with config_path.open("r", encoding="utf-8") as fh:
            FLOW_CONFIG = json.load(fh)
    except Exception as exc:
        FLOW_CONFIG = {}
        if DEBUG_ENABLED:
            print(f"[SDK_WORKER] Failed to load flowviz_config.json ({exc}). Using defaults.", file=sys.stderr)
        return

    ignore_entries = FLOW_CONFIG.get("ignore_files", [])
    IGNORED_PATHS = _resolve_config_paths(game_dir, ignore_entries)
    force_entries = FLOW_CONFIG.get("force_rpyc_files", [])
    FORCE_RPYC_PATHS = _resolve_config_paths(game_dir, force_entries)

    if DEBUG_ENABLED:
        ignore_list = ", ".join(str(path) for path in sorted(IGNORED_PATHS)) or "<none>"
        force_list = ", ".join(str(path) for path in sorted(FORCE_RPYC_PATHS)) or "<none>"
        print(f"[SDK_WORKER] flowviz_config.json loaded from {config_path}", file=sys.stderr)
        print(f"[SDK_WORKER] Ignored files: {ignore_list}", file=sys.stderr)
        print(f"[SDK_WORKER] Forced .rpyc files: {force_list}", file=sys.stderr)


def _resolve_config_paths(game_dir: Path, entries: Any) -> Set[Path]:
    resolved: Set[Path] = set()
    if not isinstance(entries, list):
        return resolved

    for entry in entries:
        if not isinstance(entry, str) or not entry.strip():
            continue
        entry_path = Path(entry.strip())
        if not entry_path.is_absolute():
            candidate = game_dir / entry_path
        else:
            candidate = entry_path
        try:
            resolved.add(candidate.resolve())
        except OSError:
            resolved.add(candidate)
    return resolved


def _is_ignored_absolute(path: Path) -> bool:
    try:
        candidate = path.resolve()
    except OSError:
        candidate = path
    return candidate in IGNORED_PATHS


def _is_force_rpyc_absolute(path: Path) -> bool:
    try:
        candidate = path.resolve()
    except OSError:
        candidate = path
    return candidate in FORCE_RPYC_PATHS


def _is_within_game_dir(path: Path) -> bool:
    if GAME_DIR is None:
        return True
    try:
        path.resolve().relative_to(GAME_DIR)
        return True
    except Exception:
        return False


def _next_available_suffix(path: Path, suffix: str) -> Path:
    candidate = path.with_suffix(path.suffix + suffix)
    counter = 1
    while candidate.exists():
        candidate = path.with_suffix(path.suffix + f"{suffix}{counter}")
        counter += 1
    return candidate


if __name__ == "__main__":
    main()

