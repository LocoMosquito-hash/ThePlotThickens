"""Host-side Ren'Py SDK flow builder (subprocess-based)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from parser import (
    LabelNode,
    LabelFlow,
    MenuNode,
    MenuChoice,
    ScreenElement,
    ScreenStructure,
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

    # Public -----------------------------------------------------------------

    def build(self, project_path: str) -> Dict[str, LabelNode]:
        project_root = self._resolve_project_root(Path(project_path))
        cmd = [
            str(self.sdk_python),
            str(self.worker_script),
            str(project_root),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise SDKFlowBuilderError(
                f"SDK worker failed (exit {result.returncode}).\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )

        try:
            payload = json.loads(result.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise SDKFlowBuilderError(f"Invalid JSON from SDK worker: {exc}\nOutput:\n{result.stdout}") from exc

        return self._construct_flow_graph(payload)

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
            structure = ScreenStructure(
                screen_name=screen_name,
                file_path=screen.get("file_path", ""),
                line_number=screen.get("line_number", 0),
                elements=[
                    ScreenElement(
                        element_type=elem.get("element_type", ""),
                        text=elem.get("text"),
                        destination=elem.get("destination"),
                        action_type=elem.get("action_type"),
                        file_path=elem.get("file_path", ""),
                        line_number=elem.get("line_number", 0),
                    )
                    for elem in screen.get("elements", [])
                ],
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


