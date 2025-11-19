#!/usr/bin/env python3
"""
Standalone diagnostic script for the SDK flow builder.

Usage:
    python debug_sdk_flow_builder.py "T:/AG/LastCall-0.4-pc"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Fix Windows stdout encoding when mixing emojis/logs
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app" / "renpy-source-api"
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(APP_DIR.parent))

from sdk_flow_graph_builder import SDKFlowGraphBuilder, SDKFlowBuilderError  # type: ignore  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the SDK flow builder in isolation.")
    parser.add_argument(
        "project_path",
        type=Path,
        help="Path to the Ren'Py project (either root or its game/ folder).",
    )
    args = parser.parse_args()

    builder = SDKFlowGraphBuilder()
    if not builder.is_available:
        raise SDKFlowBuilderError(
            f"SDK builder unavailable: {builder.initialization_error or 'unknown reason'}"
        )

    project_path = str(args.project_path)
    print(f"[DEBUG] Running SDK flow builder for: {project_path}")
    graph = builder.build_flow_graph(project_path)
    label_count = sum(1 for key in graph if not key.startswith("_"))

    print(f"[DEBUG] Flow graph keys: {len(graph)} entries ({label_count} labels)")
    print("[DEBUG] Sample labels:")
    for idx, (key, node) in enumerate(graph.items()):
        if key.startswith("_"):
            continue
        print(f"  - {key} ({len(node.outgoing_flows)} outgoing, {len(node.incoming_flows)} incoming)")
        if idx >= 4:
            break


if __name__ == "__main__":
    main()


