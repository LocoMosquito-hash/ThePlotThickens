"""Host-side Ren'Py SDK flow builder (subprocess-based)."""

from __future__ import annotations

import json
import subprocess
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from parser import (
    LabelNode,
    LabelFlow,
    MenuNode,
    MenuChoice,
    ScreenElement,
    ScreenStructure,
)


_PARSE_ERROR_RE = re.compile(
    r"""
    (?:
        File\s+"(?P<file1>[^"]+\.rpy)"\s*,\s*line\s+(?P<line1>\d+)
        |
        \((?P<file2>[^)]+\.rpy)\s*,\s*line\s+(?P<line2>\d+)\)
        |
        in\s+file\s+(?P<file3>[^\s,:]+\.rpy)
    )
    """,
    re.IGNORECASE | re.MULTILINE,
)

_LABEL_DEF_RE = re.compile(r"^\s*label\s+([A-Za-z_][\w.]*)\s*:")
_SCREEN_CALL_RE = re.compile(r"^\s*(call|show)\s+screen\s+([A-Za-z_][\w.]+)")
_SHOW_MENU_CALL_RE = re.compile(
    r"""^\s*
        (?:\$|python:)?
        \s*
        (?:
            renpy\.(?:ShowMenu|show_menu)
            |
            ShowMenu
        )
        \s*\(\s*
        ["'](?P<screen>[A-Za-z_][\w.]*)["']
        \s*\)
    """,
    re.IGNORECASE | re.VERBOSE,
)


class SDKFlowBuilderError(RuntimeError):
    """Raised when the Ren'Py SDK flow builder fails."""


class SDKFlowBuilder:
    """
    Build a Ren'Py flow graph by invoking the official SDK in a subprocess.
    """

    def __init__(self, sdk_dir: Optional[Path] = None):
        base_dir = Path(__file__).parent
        default_sdk = base_dir / "renpy_sdk" / "renpy-8.4.0-sdk"
        self.sdk_dir = Path(sdk_dir) if sdk_dir else default_sdk
        if not self.sdk_dir.exists():
            raise SDKFlowBuilderError(f"Ren'Py SDK directory not found: {self.sdk_dir}")

        self.sdk_python = self.sdk_dir / "lib" / "py3-windows-x86_64" / "python.exe"
        if not self.sdk_python.exists():
            raise SDKFlowBuilderError(f"Ren'Py SDK python executable missing: {self.sdk_python}")

        self.worker_script = Path(__file__).with_name("sdk_flow_builder_worker.py")
        if not self.worker_script.exists():
            raise SDKFlowBuilderError(f"SDK worker script missing: {self.worker_script}")

        self._debug_enabled = os.environ.get("SDK_FLOW_DEBUG") == "1"
        self._max_attempts = 5

    # Public -----------------------------------------------------------------

    def build(self, project_path: str) -> Dict[str, LabelNode]:
        project_root = self._resolve_project_root(Path(project_path))
        cmd = [
            str(self.sdk_python),
            str(self.worker_script),
            str(project_root),
        ]

        hidden_sources: List[Tuple[Path, Path]] = []
        hidden_originals: Set[Path] = set()
        attempts = 0
        last_error: Optional[str] = None

        try:
            while attempts < self._max_attempts:
                attempts += 1
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    try:
                        payload = json.loads(result.stdout or "{}")
                    except json.JSONDecodeError as exc:
                        raise SDKFlowBuilderError(f"Invalid JSON from SDK worker: {exc}\nOutput:\n{result.stdout}") from exc
                    flow_graph = self._construct_flow_graph(payload)
                    self._augment_screen_calls(flow_graph, project_root)
                    return flow_graph

                error_message = self._format_worker_failure(result, attempts)
                last_error = error_message

                offending = self._extract_error_paths(result.stdout, result.stderr, project_root)
                if offending:
                    game_dir = project_root / "game"
                    new_hidden = self._hide_problem_sources(
                        offending,
                        game_dir,
                        hidden_sources,
                        hidden_originals,
                    )
                    if new_hidden:
                        continue
                    offender_list = ", ".join(str(path) for path, _ in offending)
                    raise SDKFlowBuilderError(
                        f"Parse errors reported in: {offender_list}\n{error_message}"
                    )

                raise SDKFlowBuilderError(error_message)

            raise SDKFlowBuilderError(
                f"SDK worker failed after {self._max_attempts} attempts.\nLast error:\n{last_error or 'unknown'}"
            )
        finally:
            self._restore_hidden_files(hidden_sources, hidden_originals)

    # Deserialization helpers -----------------------------------------------

    def _construct_flow_graph(self, payload: Dict[str, Any]) -> Dict[str, LabelNode]:
        flow_graph: Dict[str, LabelNode] = {}

        for label_payload in payload.get("labels", []):
            node = self._deserialize_label_node(label_payload)
            flow_graph[node.name] = node

        self._populate_incoming_flows(flow_graph)

        screens = self._deserialize_screens(payload.get("screens", []))
        flow_graph["_screen_structures"] = {screen.screen_name: screen for screen in screens}
        flow_graph["_named_menu_registry"] = {}
        return flow_graph

    def _deserialize_label_node(self, data: Dict[str, Any]) -> LabelNode:
        node = LabelNode(
            name=data["name"],
            file_path=data.get("file_path", ""),
            line_number=data.get("line_number", 0),
        )

        node.has_dialogue = data.get("has_dialogue", False)
        node.is_dead_end = data.get("is_dead_end", False)
        node.flow_complexity = data.get("flow_complexity", 0)
        node.screen_calls = data.get("screen_calls", [])

        node.outgoing_flows = [self._deserialize_flow(flow) for flow in data.get("outgoing_flows", [])]
        node.menu_nodes = [self._deserialize_menu(menu) for menu in data.get("menu_nodes", [])]
        node.has_menu = len(node.menu_nodes) > 0
        node.menu_count = len(node.menu_nodes)

        return node

    def _deserialize_flow(self, data: Dict[str, Any]) -> LabelFlow:
        return LabelFlow(
            source_label=data.get("source_label"),
            target_label=data.get("target_label", ""),
            flow_type=data.get("flow_type", "jump"),
            file_path=data.get("file_path", ""),
            line_number=data.get("line_number", 0),
            context=data.get("context"),
            condition=data.get("condition"),
        )

    def _deserialize_menu(self, data: Dict[str, Any]) -> MenuNode:
        menu_node = MenuNode(
            node_id=data.get("node_id", ""),
            name=data.get("name", ""),
            parent_label=data.get("parent_label", ""),
            menu_index=data.get("menu_index", 0),
            file_path=data.get("file_path", ""),
            line_number=data.get("line_number", 0),
            prompt=data.get("prompt"),
            choices=[],
            total_choices=len(data.get("choices", [])),
            is_nested=data.get("is_nested", False),
        )

        choices = []
        for idx, choice_payload in enumerate(data.get("choices", [])):
            choice = self._deserialize_choice(choice_payload, idx)
            choices.append(choice)
        menu_node.choices = choices
        menu_node.total_choices = len(choices)
        menu_node.has_conditions = any(choice.has_condition for choice in choices)
        return menu_node

    def _deserialize_choice(self, data: Dict[str, Any], choice_index: int) -> MenuChoice:
        choice = MenuChoice(
            text=data.get("text", ""),
            condition=data.get("condition"),
            destination=data.get("destination"),
            file_path=data.get("file_path", ""),
            line_number=data.get("line_number", 0),
            choice_index=choice_index,
        )

        choice.all_destinations = data.get("all_destinations", [])
        choice.action_type = data.get("action_type")
        choice.has_condition = bool(choice.condition)
        choice.leads_to_label = data.get("leads_to_label", False)
        choice.leads_to_return = data.get("leads_to_return", False)
        choice.nested_labels = data.get("nested_labels", [])

        nested_menus = [self._deserialize_menu(nested) for nested in data.get("nested_menus", [])]
        choice.nested_menu_structures = nested_menus

        return choice

    def _deserialize_screens(self, items: List[Dict[str, Any]]) -> List[ScreenStructure]:
        structures: List[ScreenStructure] = []
        for screen in items:
            screen_name = self._normalize_screen_name(screen.get("screen_name"))
            elements = self._convert_screen_elements(screen)
            structure = ScreenStructure(
                screen_name=screen_name,
                file_path=screen.get("file_path", ""),
                line_number=screen.get("line_number", 0),
                screen_type=screen.get("screen_type") or "standard",
                elements=elements,
            )
            structures.append(structure)
        return structures

    @staticmethod
    def _normalize_screen_name(raw_name: Any) -> str:
        if isinstance(raw_name, str):
            return raw_name
        if isinstance(raw_name, (list, tuple)):
            return ":".join(str(part) for part in raw_name if part)
        return str(raw_name or "")

    def _convert_screen_elements(self, screen_payload: Dict[str, Any]) -> List[ScreenElement]:
        elements: List[ScreenElement] = []
        raw_elements = screen_payload.get("elements", [])
        for raw_element in raw_elements:
            actions = raw_element.get("actions") or []
            if not actions:
                continue
            coordinates = self._bounds_to_tuple(raw_element.get("coordinates") or raw_element.get("bounds"))
            text_value = raw_element.get("text")
            keywords = raw_element.get("keywords", [])
            condition = raw_element.get("condition")

            for action_payload in actions:
                destination = self._derive_screen_destination(action_payload)
                target_screen = action_payload.get("target_screen")
                has_label_target = isinstance(destination, str) and destination
                has_screen_target = isinstance(target_screen, str) and target_screen
                if not has_label_target and not has_screen_target:
                    continue

                element_condition = action_payload.get("condition") or condition
                screen_element = ScreenElement(
                    element_type=self._normalize_element_type(raw_element.get("element_type")),
                    text=text_value,
                    coordinates=coordinates,
                    destination=destination if has_label_target else None,
                    action_type=action_payload.get("action_type"),
                    file_path=raw_element.get("file_path", ""),
                    line_number=raw_element.get("line_number", 0),
                    condition=element_condition,
                )
                screen_element.element_index = len(elements)
                screen_element.trigger = action_payload.get("trigger")
                screen_element.raw_expression = action_payload.get("raw_expression")
                screen_element.target_screen = action_payload.get("target_screen")
                screen_element.target_url = action_payload.get("target_url")
                screen_element.target_value = action_payload.get("target_value")
                screen_element.keywords = keywords
                elements.append(screen_element)
        return elements

    @staticmethod
    def _bounds_to_tuple(bounds: Any) -> Optional[Tuple[int, int, int, int]]:
        def _validate(candidate: Iterable[Any]) -> Optional[Tuple[int, int, int, int]]:
            values: List[int] = []
            for value in candidate:
                if isinstance(value, (int, float)):
                    values.append(int(value))
            if len(values) >= 4:
                return values[0], values[1], values[2], values[3]
            return None

        if isinstance(bounds, dict):
            ordered = [bounds.get("x"), bounds.get("y"), bounds.get("width"), bounds.get("height")]
            return _validate(ordered)
        if isinstance(bounds, (list, tuple)):
            return _validate(bounds)
        return None

    @staticmethod
    def _normalize_element_type(value: Any) -> str:
        if isinstance(value, str):
            return value.lstrip("_") or "unknown"
        if value is None:
            return "unknown"
        return str(value)

    @staticmethod
    def _derive_screen_destination(action_payload: Dict[str, Any]) -> Optional[str]:
        action_type = action_payload.get("action_type")
        target_label = action_payload.get("target_label")
        if action_type in {"jump_label", "call_label", "replay_label"} and isinstance(target_label, str):
            return target_label
        return None

    def _populate_incoming_flows(self, flow_graph: Dict[str, LabelNode]) -> None:
        for node in flow_graph.values():
            if not hasattr(node, "outgoing_flows"):
                continue
            for flow in node.outgoing_flows:
                if not flow.target_label or flow.target_label == "<return>":
                    continue
                target = flow_graph.get(flow.target_label)
                if target is not None:
                    target.incoming_flows.append(flow)

    @staticmethod
    def _resolve_project_root(path: Path) -> Path:
        resolved = path.resolve()
        if (resolved / "game").is_dir():
            return resolved
        if resolved.name.lower() == "game" and resolved.is_dir():
            return resolved.parent
        raise SDKFlowBuilderError(f"Expected Ren'Py project or its /game directory, got: {path}")

    # Retry helpers ---------------------------------------------------------

    def _format_worker_failure(self, result: subprocess.CompletedProcess[str], attempt: int) -> str:
        return (
            f"SDK worker failed (exit {result.returncode}) on attempt {attempt}.\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    def _augment_screen_calls(self, flow_graph: Dict[str, LabelNode], project_root: Path) -> None:
        try:
            screen_calls = self._scan_screen_calls(project_root)
        except Exception as exc:
            if self._debug_enabled:
                print(f"[SDK_HOST] Failed to scan screen calls: {exc}", file=sys.stderr)
            return

        for label_name, screens in screen_calls.items():
            node = flow_graph.get(label_name)
            if not node:
                continue
            deduped: List[str] = []
            seen: Set[str] = set()
            for screen in screens:
                if screen not in seen:
                    seen.add(screen)
                    deduped.append(screen)
            node.screen_calls = deduped
            node.has_screen_calls = bool(deduped)

    def _scan_screen_calls(self, project_root: Path) -> Dict[str, List[str]]:
        search_root = project_root / "game"
        if not search_root.is_dir():
            search_root = project_root

        calls: Dict[str, List[str]] = {}
        for rpy_path in search_root.rglob("*.rpy"):
            if self._should_skip_screen_file(rpy_path, search_root):
                continue
            current_label: Optional[str] = None
            try:
                content = rpy_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = rpy_path.read_text(encoding="latin-1")
            except OSError:
                continue

            for raw_line in content.splitlines():
                label_match = _LABEL_DEF_RE.match(raw_line)
                if label_match:
                    current_label = label_match.group(1)
                    continue

                if not current_label:
                    continue

                stripped = raw_line.strip()
                if not stripped or stripped.startswith("#"):
                    continue

                call_match = _SCREEN_CALL_RE.match(stripped)
                if call_match:
                    screen_name = call_match.group(2)
                    calls.setdefault(current_label, []).append(screen_name)
                    continue

                showmenu_match = _SHOW_MENU_CALL_RE.match(raw_line)
                if showmenu_match:
                    screen_name = showmenu_match.group("screen")
                    if screen_name:
                        calls.setdefault(current_label, []).append(screen_name)

        return calls

    @staticmethod
    def _should_skip_screen_file(path: Path, root: Path) -> bool:
        try:
            relative = path.relative_to(root)
        except ValueError:
            relative = path
        lowered_parts = [part.lower() for part in relative.parts]
        if "renpy" in lowered_parts:
            return True
        if "0x52-urm" in lowered_parts:
            return True
        if "tl" in lowered_parts:
            return True
        return False

    def _extract_error_paths(
        self,
        stdout_text: str,
        stderr_text: str,
        project_root: Path,
    ) -> List[Tuple[Path, int]]:
        combined = f"{stdout_text}\n{stderr_text}"
        matches = _PARSE_ERROR_RE.finditer(combined)
        paths: List[Tuple[Path, int]] = []
        seen: Set[Path] = set()
        for match in matches:
            filename = match.group("file1") or match.group("file2") or match.group("file3")
            if not filename:
                continue
            line_text = match.group("line1") or match.group("line2")
            line_number = int(line_text) if line_text and line_text.isdigit() else 0
            candidate = Path(filename)
            try:
                if not candidate.is_absolute():
                    candidate = (project_root / candidate).resolve()
                else:
                    candidate = candidate.resolve()
            except OSError:
                continue
            if candidate in seen:
                continue
            seen.add(candidate)
            paths.append((candidate, line_number))
        return paths

    def _hide_problem_sources(
        self,
        offending: List[Tuple[Path, int]],
        game_dir: Path,
        hidden_pairs: List[Tuple[Path, Path]],
        hidden_set: Set[Path],
    ) -> List[Tuple[Path, Path]]:
        new_hidden: List[Tuple[Path, Path]] = []
        for path, _ in offending:
            if path in hidden_set:
                continue
            if path.suffix.lower() != ".rpy":
                continue
            if not self._is_within_directory(path, game_dir):
                continue
            if not path.exists():
                continue
            compiled = path.with_suffix(path.suffix + "c")
            if not compiled.exists():
                continue
            hidden_path = self._next_available_suffix(path, ".flowignore")
            try:
                path.rename(hidden_path)
            except OSError:
                continue
            hidden_pairs.append((path, hidden_path))
            hidden_set.add(path)
            new_hidden.append((path, hidden_path))
        if new_hidden:
            self._log_switch(new_hidden)
        return new_hidden

    def _restore_hidden_files(
        self,
        hidden_pairs: List[Tuple[Path, Path]],
        hidden_set: Set[Path],
    ) -> None:
        for original, temp in reversed(hidden_pairs):
            try:
                if original.exists():
                    original.unlink()
                if temp.exists():
                    temp.rename(original)
            except OSError:
                continue
            finally:
                hidden_set.discard(original)

    @staticmethod
    def _next_available_suffix(path: Path, suffix: str) -> Path:
        candidate = path.with_suffix(path.suffix + suffix)
        counter = 1
        while candidate.exists():
            candidate = path.with_suffix(path.suffix + f"{suffix}{counter}")
            counter += 1
        return candidate

    @staticmethod
    def _is_within_directory(path: Path, directory: Path) -> bool:
        try:
            path.resolve().relative_to(directory)
            return True
        except Exception:
            return False

    def _log_switch(self, hidden: List[Tuple[Path, Path]]) -> None:
        if not self._debug_enabled:
            return
        pretty = ", ".join(str(original) for original, _ in hidden)
        print(f"[SDK_HOST] Switching to .rpyc for: {pretty}", file=sys.stderr)


