 #!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The Plot Thickens - Launcher

This script launches the main application or FlowViz CLI utilities.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

# Fix Unicode encoding issues on Windows
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import main as launch_application  # noqa: E402


def _build_cli_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""

    parser = argparse.ArgumentParser(
        description="The Plot Thickens launcher and tooling entry point."
    )
    subparsers = parser.add_subparsers(dest="command")

    flowviz = subparsers.add_parser(
        "flowviz-cache",
        help="Inspect slots and orchestrate FlowViz cache generation.",
    )
    flowviz.add_argument(
        "--slot-id",
        type=int,
        required=True,
        help="ID of the story slot to analyze.",
    )
    flowviz.add_argument(
        "--story-id",
        type=int,
        help="Optional story ID to validate against the slot.",
    )
    flowviz.add_argument(
        "--source-mode",
        choices=["rpyc_only", "rpy_only", "auto"],
        default="rpyc_only",
        help="Select which source files the SDK should read.",
    )
    flowviz.add_argument(
        "--config-path",
        type=str,
        help="Override path to flowviz_config.json (defaults to slot root).",
    )
    flowviz.add_argument(
        "--bundled-runtime",
        choices=["prefer", "require", "disable"],
        default="prefer",
        help="Control usage of bundled Ren'Py runtimes for analysis.",
    )
    flowviz.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Console log level for the CLI run.",
    )

    return parser


def _run_flowviz_cache(args: argparse.Namespace) -> int:
    """Dispatch the flowviz-cache subcommand."""

    from app.flowviz.cli_flowviz_cache import FlowvizCacheCLIOptions, run_flowviz_cache

    project_root = Path(__file__).resolve().parent
    config_path: Optional[Path] = Path(args.config_path).expanduser() if args.config_path else None

    options = FlowvizCacheCLIOptions(
        project_root=project_root,
        slot_id=args.slot_id,
        story_id=args.story_id,
        source_mode=args.source_mode,
        config_path=config_path,
        bundled_runtime=args.bundled_runtime,
        log_level=args.log_level,
    )
    return run_flowviz_cache(options)


def main() -> None:
    """Entry point that either launches the GUI or a CLI subcommand."""

    if len(sys.argv) == 1:
        launch_application()
        return

    parser = _build_cli_parser()
    args = parser.parse_args()

    if args.command == "flowviz-cache":
        raise SystemExit(_run_flowviz_cache(args))

    parser.print_help()


if __name__ == "__main__":
    main()