"""High-level wrapper to build flow graphs using the Ren'Py SDK."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from parser import LabelNode

from sdk_flow_builder import SDKFlowBuilder, SDKFlowBuilderError


class SDKFlowGraphBuilder:
    """
    Convenience wrapper that exposes a simple API to the rest of the app.
    """

    def __init__(self, sdk_dir: Optional[Path] = None) -> None:
        self._builder: Optional[SDKFlowBuilder] = None
        self._initialization_error: Optional[str] = None

        try:
            self._builder = SDKFlowBuilder(sdk_dir=sdk_dir)
        except SDKFlowBuilderError as exc:
            self._initialization_error = str(exc)

    @property
    def is_available(self) -> bool:
        return self._builder is not None

    @property
    def initialization_error(self) -> Optional[str]:
        return self._initialization_error

    def build_flow_graph(
        self, project_path: str, flow_config: Optional[Dict[str, object]] = None
    ) -> Dict[str, LabelNode]:
        if not self._builder:
            raise SDKFlowBuilderError(
                self._initialization_error or "SDK flow builder unavailable."
            )

        return self._builder.build(project_path, flow_config=flow_config)

