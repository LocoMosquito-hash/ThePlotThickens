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
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT_DIR = Path(__file__).parent
SDK_DIR = ROOT_DIR / "renpy_sdk" / "renpy-8.4.0-sdk"
PYTHON_STDLIB = SDK_DIR / "lib" / "python3.12"
SITE_PACKAGES = PYTHON_STDLIB / "site-packages"
STATE: Optional["_ExtractionState"] = None
DEBUG_ENABLED = os.environ.get("SDK_FLOW_DEBUG") == "1"
FREEZE_RPY_TIMESTAMPS = True
FLOW_CONFIG: Dict[str, Any] = {}
IGNORED_PATHS: Set[Path] = set()
FORCE_RPYC_PATHS: Set[Path] = set()
PROJECT_ROOT: Optional[Path] = None
GAME_DIR: Optional[Path] = None
PROCESS_RPYC_ONLY: bool = False
_HIDDEN_SOURCE_ORIGINALS: Set[Path] = set()
_FREEZE_REFERENCE_TS = datetime(2005, 1, 1, 0, 0).timestamp()


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
        return {"labels": labels, "screens": screens, "process_rpyc_only": PROCESS_RPYC_ONLY}

    def _is_label_node(self, node: Any) -> bool:
        import renpy.ast  # type: ignore

        return isinstance(node, renpy.ast.Label)

    def _collect_screens(self) -> List[Dict[str, Any]]:
        import renpy.ast  # type: ignore

        payload: List[Dict[str, Any]] = []
        seen_keys: Set[str] = set()

        if DEBUG_ENABLED:
            total_screens = sum(1 for node in self.script.namemap.values() if isinstance(node, renpy.ast.Screen))  # type: ignore[attr-defined]
            print(f"[SDK_WORKER][SCREENS] AST reported {total_screens} screen nodes.", file=sys.stderr)

        for node in self.script.namemap.values():  # type: ignore[attr-defined]
            if not isinstance(node, renpy.ast.Screen):
                continue
            if self._is_excluded_source(getattr(node, "filename", None)):
                continue
            screen_key = (getattr(node.screen, "name", ""), getattr(node, "filename", ""))
            if screen_key in seen_keys:
                continue
            try:
                analyzer = ScreenAnalyzer(node, self.project_root)
                screen_payload = analyzer.analyze()
            except Exception as exc:
                if DEBUG_ENABLED:
                    name_hint = getattr(node.screen, "name", None) if getattr(node, "screen", None) else None
                    print(
                        f"[SDK_WORKER] Failed to analyze screen '{name_hint}': {exc}",
                        file=sys.stderr,
                    )
                continue
            seen_keys.add(screen_key)
            if not self._is_project_screen(screen_payload.get("screen_name", ""), screen_payload.get("file_path", "")):
                continue
            if DEBUG_ENABLED:
                print(
                    f"[SDK_WORKER][SCREENS] Captured screen '{screen_payload.get('screen_name')}' "
                    f"from {screen_payload.get('file_path')}",
                    file=sys.stderr,
                )
            payload.append(screen_payload)
        return payload

    def _build_exclusion_roots(self) -> List[Path]:
        roots: List[Path] = []
        candidates = [
            self.project_root / "renpy",
            self.project_root / "game" / "0x52-URM",
            self.project_root / "0x52-URM",
            self.project_root / "game" / "tl",
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
            label_name = getattr(stmt, "name", None)
            if label_name == self.label_name:
                return True
            if isinstance(label_name, str) and label_name.startswith("_call_"):
                # Inline helper labels inserted by Ren'Py for `call ... from _call_*`.
                # These labels conceptually belong to the current block, so keep scanning.
                return True
            self._record_fallthrough_transition(stmt, active_condition)
            return False
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


class ScreenAnalyzer:
    def __init__(self, screen_ast: Any, project_root: Path):
        import renpy.sl2.slast  # type: ignore

        self.screen_ast = screen_ast
        self.project_root = project_root
        self.sl2 = renpy.sl2.slast  # type: ignore
        self.elements: List[Dict[str, Any]] = []
        self._debug_target: Optional[str] = None
        self.screen_name: str = ""

    def analyze(self) -> Dict[str, Any]:
        screen_obj = getattr(self.screen_ast, "screen", None)
        self.screen_name = getattr(screen_obj, "name", "") if screen_obj else ""
        file_path = self._normalize_filename(getattr(self.screen_ast, "filename", ""))
        line_number = getattr(self.screen_ast, "linenumber", 0)

        debug_screen = os.environ.get("SDK_SCREEN_DEBUG")
        should_debug = False
        if DEBUG_ENABLED:
            if file_path.lower().endswith("myscreens.rpy"):
                should_debug = True
            elif debug_screen and self.screen_name and self.screen_name == debug_screen:
                should_debug = True
        if should_debug:
            self._debug_target = self.screen_name or "<unknown>"
            print(
                f"[SDK_WORKER][SCREENS] Inspecting screen '{self._debug_target}' at {file_path}:{line_number}",
                file=sys.stderr,
            )

        if screen_obj is not None:
            self._walk_block(screen_obj, active_condition=None)

        return {
            "screen_name": self.screen_name,
            "file_path": file_path,
            "line_number": line_number,
            "elements": self.elements,
        }

    def _walk_block(self, block: Any, active_condition: Optional[str]) -> None:
        children = getattr(block, "children", None) or []
        for child in children:
            self._visit_node(child, active_condition)

    def _visit_node(self, node: Any, active_condition: Optional[str]) -> None:
        if DEBUG_ENABLED and self._debug_target is not None:
            is_disp = False
            try:
                is_disp = isinstance(node, self.sl2.SLDisplayable)
            except Exception:
                is_disp = False
            print(
                f"[SDK_WORKER][SCREENS] node type={type(node).__name__} condition={active_condition} is_displayable={is_disp}",
                file=sys.stderr,
            )

        if isinstance(node, self.sl2.SLIf):
            for cond_expr, block in node.entries:
                combined = active_condition
                if cond_expr is not None:
                    cond_text = self._stringify_sl_condition(cond_expr)
                    combined = (
                        cond_text
                        if active_condition is None
                        else f"({active_condition}) and ({cond_text})"
                    )
                self._walk_block(block, combined)
            return

        if isinstance(node, self.sl2.SLDisplayable):
            self._process_displayable(node, active_condition)
            return

        if isinstance(node, self.sl2.SLBlock):
            self._walk_block(node, active_condition)
            return

        nested_block = getattr(node, "block", None)
        if nested_block is not None:
            self._walk_block(nested_block, active_condition)

    def _process_displayable(self, displayable: Any, active_condition: Optional[str]) -> None:
        if not DEBUG_ENABLED or self._debug_target is None:
            pass

        keyword_entries = self._collect_keyword_entries(displayable, active_condition)
        keyword_names = sorted({entry["key"] for entry in keyword_entries})

        if DEBUG_ENABLED and self._debug_target is not None:
            keyword_list = ", ".join(keyword_names) if keyword_names else "<no keywords>"
            disp_obj = getattr(displayable, "displayable", None)
            if hasattr(disp_obj, "__name__"):
                disp_name = getattr(disp_obj, "__name__")
            else:
                disp_name = getattr(displayable, "name", "") or repr(disp_obj)

            print(
                f"[SDK_WORKER][SCREENS] screen={self._debug_target} displayable={disp_name} keywords={keyword_list}",
                file=sys.stderr,
            )

            for key, expr in getattr(displayable, "keyword", []):
                expr_desc = self._describe_keyword_expr(expr)
                text_attr = getattr(expr, "text", None)
                source_attr = getattr(expr, "source", None)
                expr_type = type(expr).__name__
                print(
                    f"    -> keyword '{key}' (type={expr_type}) expr={expr_desc} text_attr={text_attr!r} source_attr={source_attr!r}",
                    file=sys.stderr,
                )

        element_type = self._derive_element_type(displayable)
        element_payload: Dict[str, Any] = {
            "screen_name": self.screen_name,
            "element_type": element_type,
            "condition": active_condition,
            "keywords": keyword_names,
            "file_path": self._normalize_filename(self._safe_get_location(displayable, index=0)),
            "line_number": self._safe_get_location(displayable, index=1),
            "text": self._extract_display_text(displayable),
        }

        coordinates = self._extract_bounds(displayable)
        if coordinates:
            element_payload["coordinates"] = coordinates

        actions = self._extract_actions(keyword_entries)
        if actions:
            element_payload["actions"] = actions
            self.elements.append(element_payload)

        for child in getattr(displayable, "children", []) or []:
            self._visit_node(child, active_condition)

    @staticmethod
    def _stringify_sl_condition(condition: Any) -> str:
        try:
            import ast

            if isinstance(condition, ast.AST):
                return ast.unparse(condition)  # type: ignore[attr-defined]
        except Exception:
            pass
        return str(condition)

    @staticmethod
    def _describe_keyword_expr(expr: Any) -> str:
        try:
            import ast

            if isinstance(expr, ast.AST):
                try:
                    return ast.unparse(expr)  # type: ignore[attr-defined]
                except Exception:
                    return ast.dump(expr, include_attributes=False)
            text = getattr(expr, "text", None)
            if text:
                return text
        except Exception:
            pass
        return repr(expr)

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

    @staticmethod
    def _safe_get_location(displayable: Any, index: int) -> Any:
        location = getattr(displayable, "location", None)
        if isinstance(location, tuple) and len(location) > index:
            return location[index]
        return None

    @staticmethod
    def _derive_element_type(displayable: Any) -> str:
        disp_obj = getattr(displayable, "displayable", None)
        if hasattr(disp_obj, "__name__"):
            return getattr(disp_obj, "__name__")
        name_attr = getattr(displayable, "name", None)
        if name_attr:
            return str(name_attr)
        return "unknown"

    def _extract_display_text(self, displayable: Any) -> Optional[str]:
        text_attr = getattr(displayable, "text", None)
        if isinstance(text_attr, str):
            return text_attr
        label_attr = getattr(displayable, "label", None)
        if isinstance(label_attr, str):
            return label_attr

        for key, expr in getattr(displayable, "keyword", []) or []:
            if key in {"text", "label"}:
                literal = self._literal_from_expr(expr)
                if isinstance(literal, str):
                    return literal

        positional = getattr(displayable, "positional", None) or []
        for arg in positional:
            literal = self._literal_from_ast(arg)
            if isinstance(literal, str):
                return literal
        return None

    def _extract_bounds(self, displayable: Any) -> Optional[Tuple[int, int, int, int]]:
        positional = getattr(displayable, "positional", None)
        if not positional:
            return None

        coords: List[int] = []
        for arg in positional:
            value = self._literal_from_ast(arg)
            if isinstance(value, (list, tuple)):
                coords.extend([int(v) for v in value if isinstance(v, (int, float))])
            elif isinstance(value, (int, float)):
                coords.append(int(value))

        if len(coords) >= 4:
            return (coords[0], coords[1], coords[2], coords[3])
        return None

    def _literal_from_expr(self, expr: Any) -> Any:
        ast_node = self._coerce_expr_to_ast(expr)
        if ast_node is not None:
            return self._literal_from_ast(ast_node)
        text_attr = getattr(expr, "text", None)
        if text_attr is not None:
            return text_attr
        source_attr = getattr(expr, "source", None)
        if isinstance(source_attr, str):
            return source_attr
        return None

    def _collect_keyword_entries(
        self,
        block: Any,
        inherited_condition: Optional[str],
    ) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        for key, expr in getattr(block, "keyword", []) or []:
            entries.append({"key": key, "expr": expr, "condition": inherited_condition})

        for child in getattr(block, "children", []) or []:
            if isinstance(child, self.sl2.SLIf):
                for cond_expr, branch in getattr(child, "entries", []):
                    combined = self._combine_conditions(inherited_condition, cond_expr)
                    entries.extend(self._collect_keyword_entries(branch, combined))

        return entries

    def _combine_conditions(self, base_condition: Optional[str], new_condition_ast: Any) -> Optional[str]:
        branch_condition: Optional[str] = None
        if new_condition_ast is not None:
            branch_condition = self._stringify_sl_condition(new_condition_ast)

        if base_condition and branch_condition:
            return f"({base_condition}) and ({branch_condition})"
        return branch_condition or base_condition

    def _extract_actions(self, keyword_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        actions: List[Dict[str, Any]] = []
        for entry in keyword_entries:
            key = entry["key"]
            expr = entry["expr"]
            condition = entry.get("condition")

            if key not in {"action", "clicked", "hovered", "selected", "unhovered", "alternate"}:
                continue
            parsed_actions = self._parse_action_expression(expr)
            if not parsed_actions and DEBUG_ENABLED and self._debug_target is not None:
                expr_repr = self._describe_keyword_expr(expr)
                print(
                    f"[SDK_WORKER][SCREENS] Unable to parse action for key='{key}' expr={expr_repr}",
                    file=sys.stderr,
                )
            for parsed in parsed_actions:
                parsed["trigger"] = key
                if condition:
                    parsed["condition"] = condition
                actions.append(parsed)
        return actions

    def _parse_action_expression(self, expr: Any) -> List[Dict[str, Any]]:
        ast_node = self._coerce_expr_to_ast(expr)
        if ast_node is None:
            if DEBUG_ENABLED and self._debug_target is not None:
                expr_repr = self._describe_keyword_expr(expr)
                print(
                    f"[SDK_WORKER][SCREENS] Failed to build AST from expr={expr_repr}",
                    file=sys.stderr,
                )
            return []

        return self._interpret_action_ast(ast_node)

    def _coerce_expr_to_ast(self, expr: Any) -> Any:
        import ast

        if isinstance(expr, ast.AST):
            return expr

        for source in self._gather_expr_sources(expr):
            try:
                parsed = ast.parse(source, mode="eval")
                return parsed.body  # type: ignore[attr-defined]
            except Exception:
                continue
        return None

    @staticmethod
    def _gather_expr_sources(expr: Any) -> List[str]:
        sources: List[str] = []
        seen: Set[str] = set()

        def _add(candidate: Optional[str]) -> None:
            if not isinstance(candidate, str):
                return
            cleaned = candidate.strip()
            if not cleaned or cleaned in seen:
                return
            seen.add(cleaned)
            sources.append(cleaned)

        if isinstance(expr, str):
            _add(expr)

        for attr in ("text", "source", "expr"):
            _add(getattr(expr, attr, None))

        code_attr = getattr(expr, "code", None)
        if isinstance(code_attr, str):
            _add(code_attr)
        elif code_attr is not None:
            _add(getattr(code_attr, "source", None))

        return sources

    def _interpret_action_ast(self, node: Any) -> List[Dict[str, Any]]:
        import ast

        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            results: List[Dict[str, Any]] = []
            for child in node.elts:  # type: ignore[attr-defined]
                results.extend(self._interpret_action_ast(child))
            return results

        if isinstance(node, ast.Call):
            target_name = self._resolve_call_name(node.func)
            raw_expr = self._safe_unparse(node)
            first_arg = node.args[0] if node.args else None
            target_value = self._literal_from_ast(first_arg) if first_arg is not None else None

            action_type = "custom"
            payload: Dict[str, Any] = {"action_type": action_type, "raw_expression": raw_expr}

            if target_name in {"Jump", "renpy.jump"} and isinstance(target_value, str):
                action_type = "jump_label"
                payload.update({"action_type": action_type, "target_label": target_value})
            elif target_name in {"Call", "renpy.call"} and isinstance(target_value, str):
                action_type = "call_label"
                payload.update({"action_type": action_type, "target_label": target_value})
            elif target_name in {"Replay", "renpy.Replay"} and isinstance(target_value, str):
                action_type = "replay_label"
                payload.update({"action_type": action_type, "target_label": target_value})
            elif target_name in {"ShowMenu", "CallScreen"} and isinstance(target_value, str):
                action_type = "show_screen" if target_name == "ShowMenu" else "call_screen"
                payload.update({"action_type": action_type, "target_screen": target_value})
            elif target_name == "Return":
                payload["action_type"] = "return"
            elif target_name == "OpenURL" and isinstance(target_value, str):
                payload.update({"action_type": "open_url", "target_url": target_value})
            elif isinstance(target_value, str):
                payload["target_value"] = target_value

            return [payload]

        return []

    @staticmethod
    def _resolve_call_name(func: Any) -> str:
        import ast

        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            parts: List[str] = []
            current = func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return ""

    @staticmethod
    def _safe_unparse(node: Any) -> str:
        try:
            import ast

            return ast.unparse(node)  # type: ignore[attr-defined]
        except Exception:
            return repr(node)

    @staticmethod
    def _literal_from_ast(node: Any) -> Any:
        import ast

        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            values = [ScreenAnalyzer._literal_from_ast(child) for child in node.elts]
            if all(v is not None for v in values):
                return tuple(values) if isinstance(node, ast.Tuple) else values
        if hasattr(node, "value"):
            return getattr(node, "value")
        return None


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
    binary_hidden: List[Tuple[Path, Path]] = []
    if PROCESS_RPYC_ONLY:
        binary_hidden = _temporarily_hide_all_rpy_sources()
    hidden_force = _temporarily_hide_force_rpyc_files()
    hidden_files = _temporarily_hide_ignored_files()
    sanitized_backups = _swap_in_sanitized_scripts(project_root)

    if FREEZE_RPY_TIMESTAMPS:
        _freeze_rpy_sources(GAME_DIR if GAME_DIR is not None else project_root / "game")
    _prepare_environment()

    import renpy  # type: ignore
    import renpy.bootstrap  # type: ignore
    import renpy.arguments  # type: ignore
    import renpy.config as renpy_config  # type: ignore

    try:
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
        _restore_hidden_files(binary_hidden)

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
        should_require_compiled = not PROCESS_RPYC_ONLY
        compiled_missing = False
        if target.suffix.lower().endswith(".rpy"):
            compiled = target.with_suffix(target.suffix + "c")
            if not compiled.exists():
                compiled_missing = True
                if should_require_compiled:
                    continue
        hidden_path = _next_available_suffix(target, ".flowignore")
        try:
            target.rename(hidden_path)
            _HIDDEN_SOURCE_ORIGINALS.add(target)
            hidden.append((target, hidden_path))
            if compiled_missing and PROCESS_RPYC_ONLY:
                print(
                    f"[SDK_WORKER] process_rpyc_only: hiding {target} (compiled counterpart not found)",
                    file=sys.stderr,
                )
        except Exception:
            continue
    if hidden and DEBUG_ENABLED:
        print(f"[SDK_WORKER] Forcing .rpyc usage for {len(hidden)} files.", file=sys.stderr)
    return hidden


def _temporarily_hide_all_rpy_sources() -> List[Tuple[Path, Path]]:
    hidden: List[Tuple[Path, Path]] = []
    if GAME_DIR is None:
        return hidden

    for rpy_file in GAME_DIR.rglob("*.rpy"):
        if not rpy_file.exists():
            continue
        if rpy_file in _HIDDEN_SOURCE_ORIGINALS:
            continue
        if not _is_within_game_dir(rpy_file):
            continue
        hidden_path = _next_available_suffix(rpy_file, ".rpyconly")
        try:
            rpy_file.rename(hidden_path)
            _HIDDEN_SOURCE_ORIGINALS.add(rpy_file)
            hidden.append((rpy_file, hidden_path))
        except Exception as exc:
            print(
                f"[SDK_WORKER] process_rpyc_only: failed to hide {rpy_file}: {exc}",
                file=sys.stderr,
            )
            continue

    print(
        f"[SDK_WORKER] process_rpyc_only: hid {len(hidden)} .rpy source files before bootstrap.",
        file=sys.stderr,
    )
    return hidden


def _freeze_rpy_sources(game_dir: Path) -> None:
    if not game_dir.exists():
        if DEBUG_ENABLED:
            print(f"[SDK_WORKER] Freeze requested but game dir missing: {game_dir}", file=sys.stderr)
        return

    total = 0
    for rpy_file in game_dir.rglob("*.rpy"):
        if not rpy_file.is_file():
            continue
        try:
            stat_result = rpy_file.stat()
            if stat_result.st_mtime <= _FREEZE_REFERENCE_TS:
                continue
            os.utime(rpy_file, (_FREEZE_REFERENCE_TS, _FREEZE_REFERENCE_TS))
            total += 1
        except OSError as exc:
            if DEBUG_ENABLED:
                print(f"[SDK_WORKER] Failed to freeze timestamp for {rpy_file}: {exc}", file=sys.stderr)
            continue

    if FREEZE_RPY_TIMESTAMPS:
        freeze_date = datetime.fromtimestamp(_FREEZE_REFERENCE_TS).date()
        print(
            f"[SDK_WORKER] Freeze timestamps enabled: adjusted {total} .rpy files to {freeze_date}",
            file=sys.stderr,
        )


def _load_flowviz_config(project_root: Path) -> None:
    global FLOW_CONFIG, IGNORED_PATHS, FORCE_RPYC_PATHS, GAME_DIR, PROJECT_ROOT, PROCESS_RPYC_ONLY
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

    print(f"[SDK_WORKER] flowviz_config.json file found at {config_path}", file=sys.stderr)

    try:
        with config_path.open("r", encoding="utf-8") as fh:
            FLOW_CONFIG = json.load(fh)
        print("[SDK_WORKER] flowviz_config.json parsed successfully.", file=sys.stderr)
    except Exception as exc:
        FLOW_CONFIG = {}
        print(f"[SDK_WORKER] flowviz_config.json parse error: {exc}", file=sys.stderr)
        return

    ignore_entries = FLOW_CONFIG.get("ignore_files", [])
    IGNORED_PATHS = _resolve_config_paths(game_dir, ignore_entries)
    force_entries = FLOW_CONFIG.get("force_rpyc_files", [])
    FORCE_RPYC_PATHS = _resolve_config_paths(game_dir, force_entries)

    ignore_list = ", ".join(str(path) for path in sorted(IGNORED_PATHS)) or "<none>"
    force_list = ", ".join(str(path) for path in sorted(FORCE_RPYC_PATHS)) or "<none>"
    print(f"[SDK_WORKER] Ignored files: {ignore_list}", file=sys.stderr)
    print(f"[SDK_WORKER] Forced .rpyc files: {force_list}", file=sys.stderr)
    PROCESS_RPYC_ONLY = bool(FLOW_CONFIG.get("process_rpyc_only", False))
    if PROCESS_RPYC_ONLY:
        print("[SDK_WORKER] process_rpyc_only enabled: only .rpyc files will be processed.", file=sys.stderr)
        try:
            all_sources = {path.resolve() for path in game_dir.rglob("*.rpy")}
        except Exception:
            all_sources = set(game_dir.rglob("*.rpy"))
        FORCE_RPYC_PATHS.update(all_sources)


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

