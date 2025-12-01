"""Command-line helpers for FlowViz slot cache operations."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from app import db_sqlite

FlowSourceMode = Literal["rpyc_only", "rpy_only", "auto"]
RuntimePreference = Literal["prefer", "require", "disable"]

RENPY_API_DIR = Path(__file__).resolve().parents[1] / "renpy-source-api"
if str(RENPY_API_DIR) not in sys.path:
    sys.path.insert(0, str(RENPY_API_DIR))

from runtime_locator import BundledPythonRuntime, locate_bundled_python  # type: ignore  # noqa: E402


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

    runtime = _select_runtime(slot_path, options.bundled_runtime, logger)
    if runtime is None:
        return 1

    payload = _run_sdk_worker(
        project_root=slot_path,
        cache_dir=cache_dir,
        runtime=runtime,
        source_mode=options.source_mode,
        logger=logger,
    )
    if payload is None:
        return 1

    payload_path = cache_dir / "sdk_payload.json"
    payload_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("SDK payload saved to %s", payload_path)

    logger.info("flowviz-cache CLI invocation completed successfully.")
    return 0


@dataclass
class RuntimeSelection:
    """Active runtime information for SDK worker execution."""

    mode: Literal["bundled", "sdk"]
    python_executable: Path
    sdk_base: Path
    bundled: Optional[BundledPythonRuntime] = None


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


def _select_runtime(
    slot_path: Path,
    preference: RuntimePreference,
    logger: logging.Logger,
) -> Optional[RuntimeSelection]:
    """Determine whether to use the bundled runtime or fallback SDK."""

    project_root = slot_path
    if preference != "disable":
        runtime = locate_bundled_python(project_root)
        if runtime:
            major_version = _probe_python_major(runtime)
            if major_version is not None and major_version < 3:
                if preference == "require":
                    logger.error(
                        "Bundled runtime is Python %s, but only Python 3 runtimes are supported right now.",
                        major_version,
                    )
                    return None
                logger.info(
                    "Detected Python %s bundled runtime; falling back to embedded SDK until Py2 worker parity is ready.",
                    major_version,
                )
            elif runtime.renpy_engine_dir is None:
                logger.warning(
                    "Bundled runtime found (%s) but missing 'renpy/' directory; falling back to SDK.",
                    runtime.descriptor,
                )
            elif major_version is None or major_version >= 3:
                logger.info(
                    "Using bundled runtime '%s' at %s",
                    runtime.descriptor,
                    runtime.python_executable,
                )
                return RuntimeSelection(
                    mode="bundled",
                    python_executable=runtime.python_executable,
                    sdk_base=runtime.root_dir,
                    bundled=runtime,
                )
        elif preference == "require":
            logger.error(
                "Bundled runtime required but not found under %s.",
                project_root,
            )
            return None

    elif preference == "require":
        logger.error("Bundled runtime required but not found under %s.", project_root)
        return None

    sdk_base = RENPY_API_DIR / "renpy_sdk" / "renpy-8.4.0-sdk"
    python_executable = sdk_base / "lib" / "py3-windows-x86_64" / "python.exe"
    if not python_executable.exists():
        logger.error("Embedded Ren'Py SDK python executable missing: %s", python_executable)
        return None
    logger.info("Using embedded Ren'Py SDK runtime at %s", python_executable)
    return RuntimeSelection(mode="sdk", python_executable=python_executable, sdk_base=sdk_base)


def _run_sdk_worker(
    project_root: Path,
    cache_dir: Path,
    runtime: RuntimeSelection,
    source_mode: FlowSourceMode,
    logger: logging.Logger,
) -> Optional[Dict[str, Any]]:
    """Invoke the SDK worker and return the parsed JSON payload."""

    worker_script = RENPY_API_DIR / "sdk_flow_builder_worker.py"
    if not worker_script.exists():
        logger.error("SDK worker script not found at %s", worker_script)
        return None

    cmd = [str(runtime.python_executable), str(worker_script), str(project_root)]
    env = os.environ.copy()
    env["FLOW_SOURCE_MODE"] = source_mode
    if runtime.mode == "bundled" and runtime.bundled is not None:
        _apply_bundled_runtime_env(runtime.bundled, env)
    else:
        env.pop("FLOW_BUNDLED_RUNTIME", None)
        env.pop("FLOW_BUNDLED_RENPY_BASE", None)
        env.pop("FLOW_BUNDLED_RENPY_DIR", None)
        env.pop("FLOW_BUNDLED_LAUNCHER", None)
        env.pop("PYTHONHOME", None)
        env.pop("FLOW_PYTHON_STDLIB", None)

    logger.debug("Executing SDK worker: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(project_root))
    log_stdout = cache_dir / "sdk_worker_stdout.log"
    log_stderr = cache_dir / "sdk_worker_stderr.log"
    log_stdout.write_text(result.stdout or "", encoding="utf-8", errors="ignore")
    log_stderr.write_text(result.stderr or "", encoding="utf-8", errors="ignore")
    logger.debug("SDK worker wrote stdout to %s and stderr to %s", log_stdout, log_stderr)

    if result.returncode != 0:
        logger.error(
            "SDK worker failed with exit code %s. See %s for details.",
            result.returncode,
            log_stderr,
        )
        return None

    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse SDK worker output: %s", exc)
        return None

    logger.info(
        "SDK worker completed successfully (%d labels, %d screens).",
        len(payload.get("labels", [])),
        len(payload.get("screens", [])),
    )
    return payload


def _apply_bundled_runtime_env(runtime: BundledPythonRuntime, env: Dict[str, str]) -> None:
    """Populate environment variables required for bundled runtimes."""

    env["FLOW_BUNDLED_RUNTIME"] = "1"
    env["FLOW_BUNDLED_RENPY_BASE"] = str(runtime.root_dir)
    if runtime.renpy_engine_dir:
        env["FLOW_BUNDLED_RENPY_DIR"] = str(runtime.renpy_engine_dir)
    if runtime.launcher_path:
        env["FLOW_BUNDLED_LAUNCHER"] = str(runtime.launcher_path)
    if runtime.platform_dir.exists():
        env["PYTHONHOME"] = str(runtime.platform_dir)
        env["PATH"] = str(runtime.platform_dir) + os.pathsep + env.get("PATH", "")
        env.setdefault("PYTHONOPTIMIZE", "2")

    stdlib_candidates: List[Path] = []
    platform_lib = runtime.platform_dir / "Lib"
    if platform_lib.exists():
        stdlib_candidates.append(platform_lib)
        site_packages = platform_lib / "site-packages"
        if site_packages.exists():
            stdlib_candidates.append(site_packages)
    legacy_stdlib = runtime.root_dir / "pythonlib2.7"
    if legacy_stdlib.exists():
        stdlib_candidates.append(legacy_stdlib)

    if stdlib_candidates:
        combined = os.pathsep.join(str(path) for path in stdlib_candidates)
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{combined}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else combined
        )
        env["FLOW_PYTHON_STDLIB"] = str(stdlib_candidates[0])


def _probe_python_major(runtime: BundledPythonRuntime) -> Optional[int]:
    """Determine the major version of a bundled runtime."""

    env = os.environ.copy()
    _apply_bundled_runtime_env(runtime, env)
    probe = subprocess.run(
        [str(runtime.python_executable), "-c", "import sys; print(sys.version_info[0])"],
        capture_output=True,
        text=True,
        env=env,
    )
    if probe.returncode != 0:
        return None
    text = (probe.stdout or "").strip()
    try:
        return int(text)
    except ValueError:
        return None

