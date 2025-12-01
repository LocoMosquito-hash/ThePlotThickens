"""Command-line helpers for FlowViz slot cache operations."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Literal, Optional

from app import db_sqlite

FlowSourceMode = Literal["rpyc_only", "rpy_only", "auto"]
RuntimePreference = Literal["prefer", "require", "disable"]


@dataclass
class FlowvizCacheCLIOptions:
    """Container for the `flowviz-cache` CLI arguments."""

    project_root: Path
    slot_id: int
    story_id: Optional[int]
    source_mode: FlowSourceMode
    config_path: Optional[Path]
    bundled_runtime: RuntimePreference
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]


@dataclass
class FlowvizConfigSnapshot:
    """Represents the contents of flowviz_config.json."""

    ignore_files: List[str] = field(default_factory=list)
    force_rpyc_files: List[str] = field(default_factory=list)
    force_source_files: List[str] = field(default_factory=list)
    path: Optional[Path] = None


def run_flowviz_cache(options: FlowvizCacheCLIOptions) -> int:
    """Entry point for the `flowviz-cache` CLI subcommand."""

    db_path = options.project_root / "the_plot_thickens.db"
    if not db_path.exists():
        print(f"[flowviz-cache] Database not found at {db_path}")
        return 1

    slot_record, story_record = _load_slot_and_story(db_path, options.slot_id, options.story_id)
    if slot_record is None or story_record is None:
        return 1

    slot_path = Path(slot_record["destination_path"]).expanduser().resolve()
    if not slot_path.exists():
        print(f"[flowviz-cache] Slot path does not exist: {slot_path}")
        return 1

    cache_dir = slot_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    log_file = cache_dir / "flowviz_cache.log"
    logger = _configure_logging(log_file, options.log_level)

    config_snapshot = _load_flowviz_config(options.config_path, slot_path, logger)

    _print_summary(
        story_record=story_record,
        slot_record=slot_record,
        slot_path=slot_path,
        cache_dir=cache_dir,
        config_snapshot=config_snapshot,
        options=options,
    )

    logger.info("flowviz-cache CLI scaffold completed successfully.")
    return 0


def _load_slot_and_story(
    db_path: Path,
    slot_id: int,
    story_id: Optional[int],
) -> tuple[Optional[dict], Optional[dict]]:
    """Fetch slot and story records, validating optional story_id."""

    connection = db_sqlite.create_connection(str(db_path))
    try:
        slot_record = db_sqlite.get_story_slot(connection, slot_id)
        if not slot_record:
            print(f"[flowviz-cache] Slot with ID {slot_id} was not found.")
            return None, None

        resolved_story_id = slot_record["story_id"]
        if story_id is not None and story_id != resolved_story_id:
            print(
                "[flowviz-cache] Story ID mismatch: provided "
                f"{story_id}, but slot belongs to story {resolved_story_id}."
            )
            return None, None

        story_record = db_sqlite.get_story(connection, resolved_story_id)
        if not story_record:
            print(f"[flowviz-cache] Story with ID {resolved_story_id} was not found.")
            return None, None

        return slot_record, story_record
    finally:
        connection.close()


def _configure_logging(log_file: Path, console_level: str) -> logging.Logger:
    """Set up console + file logging for flowviz-cache runs."""

    logger = logging.getLogger("flowviz.cache")
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    )
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(getattr(logging, console_level, logging.INFO))
    stream_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(stream_handler)

    logger.debug("Logging initialized. File: %s", log_file)
    return logger


def _load_flowviz_config(
    override_path: Optional[Path],
    slot_path: Path,
    logger: logging.Logger,
) -> FlowvizConfigSnapshot:
    """Load flowviz_config.json from slot or override path."""

    candidate = override_path or (slot_path / "flowviz_config.json")

    if candidate is None or not candidate.exists():
        logger.info("No flowviz_config.json found (expected at %s).", candidate)
        return FlowvizConfigSnapshot(path=candidate)

    try:
        raw = json.loads(candidate.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to parse %s: %s", candidate, exc)
        return FlowvizConfigSnapshot(path=candidate)

    snapshot = FlowvizConfigSnapshot(
        ignore_files=_clean_list(raw.get("ignore_files", [])),
        force_rpyc_files=_clean_list(raw.get("force_rpyc_files", [])),
        force_source_files=_clean_list(raw.get("force_source_files", [])),
        path=candidate,
    )
    logger.debug("Loaded flowviz_config.json: %s", snapshot)
    return snapshot


def _clean_list(values: object) -> List[str]:
    """Normalize JSON entries into a clean list of strings."""

    if not isinstance(values, list):
        return []
    cleaned: List[str] = []
    for entry in values:
        if isinstance(entry, str):
            normalized = entry.strip()
            if normalized:
                cleaned.append(normalized)
    return cleaned


def _print_summary(
    story_record: dict,
    slot_record: dict,
    slot_path: Path,
    cache_dir: Path,
    config_snapshot: FlowvizConfigSnapshot,
    options: FlowvizCacheCLIOptions,
) -> None:
    """Emit a quick summary of the resolved inputs."""

    summary_lines = [
        "FlowViz cache scaffolding",
        f" Story: {story_record.get('title', 'Unknown')} (id={story_record.get('id')})",
        f" Slot: #{slot_record.get('slot_number')} (id={slot_record.get('id')})",
        f" Slot path: {slot_path}",
        f" Cache dir: {cache_dir}",
        f" Source mode: {options.source_mode}",
        f" Runtime preference: {options.bundled_runtime}",
        f" Config path: {config_snapshot.path or 'not set'}",
        f"   ignore_files={len(config_snapshot.ignore_files)}, "
        f"force_rpyc_files={len(config_snapshot.force_rpyc_files)}, "
        f"force_source_files={len(config_snapshot.force_source_files)}",
        " Next step: wire SDK runtime + normalization to emit metadata.db",
    ]

    print("\n".join(summary_lines))

