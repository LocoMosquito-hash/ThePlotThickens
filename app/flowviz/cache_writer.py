"""Helpers to persist FlowViz SDK payloads into per-slot cache databases."""

from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from app import __version__ as APP_VERSION


def write_cache_database(
    cache_dir: Path,
    payload: Dict[str, Any],
    *,
    story_record: Dict[str, Any],
    slot_record: Dict[str, Any],
    source_mode: str,
    runtime_mode: str,
    runtime_descriptor: str,
    runtime_executable: str,
) -> Path:
    """Serialize the SDK payload into a SQLite cache under the given slot."""

    cache_dir.mkdir(parents=True, exist_ok=True)
    temp_path = cache_dir / "metadata.tmp"
    final_path = cache_dir / "metadata.db"
    if temp_path.exists():
        temp_path.unlink()

    conn = sqlite3.connect(temp_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        _initialize_schema(conn)
        _persist_cache_meta(
            conn,
            payload=payload,
            story_record=story_record,
            slot_record=slot_record,
            source_mode=source_mode,
            runtime_mode=runtime_mode,
            runtime_descriptor=runtime_descriptor,
            runtime_executable=runtime_executable,
        )
        _persist_labels(conn, payload.get("labels", []), slot_record["id"])
        _persist_screens(conn, payload.get("screens", []), slot_record["id"])
        conn.commit()
    finally:
        conn.close()

    shutil.move(str(temp_path), str(final_path))
    return final_path


def _initialize_schema(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cache_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            file_path TEXT,
            line_number INTEGER,
            has_dialogue INTEGER,
            is_dead_end INTEGER,
            flow_complexity INTEGER,
            metadata_json TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS menus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER NOT NULL,
            label_name TEXT NOT NULL,
            menu_identifier TEXT,
            menu_index INTEGER,
            prompt TEXT,
            file_path TEXT,
            line_number INTEGER,
            is_nested INTEGER,
            metadata_json TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS menu_choices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER NOT NULL,
            menu_id INTEGER NOT NULL,
            choice_index INTEGER,
            text TEXT,
            destination TEXT,
            all_destinations TEXT,
            file_path TEXT,
            line_number INTEGER,
            has_condition INTEGER,
            leads_to_label INTEGER,
            metadata_json TEXT,
            FOREIGN KEY (menu_id) REFERENCES menus(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER NOT NULL,
            source_label TEXT NOT NULL,
            target_label TEXT,
            flow_type TEXT,
            file_path TEXT,
            line_number INTEGER,
            condition TEXT,
            context TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS screens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER NOT NULL,
            screen_name TEXT,
            screen_type TEXT,
            file_path TEXT,
            line_number INTEGER,
            metadata_json TEXT
        )
        """
    )
    conn.commit()


def _persist_cache_meta(
    conn: sqlite3.Connection,
    *,
    payload: Dict[str, Any],
    story_record: Dict[str, Any],
    slot_record: Dict[str, Any],
    source_mode: str,
    runtime_mode: str,
    runtime_descriptor: str,
    runtime_executable: str,
) -> None:
    cursor = conn.cursor()
    meta_entries = {
        "story_id": str(story_record.get("id")),
        "story_title": story_record.get("title") or "",
        "slot_id": str(slot_record.get("id")),
        "slot_number": str(slot_record.get("slot_number")),
        "source_mode": source_mode,
        "runtime_mode": runtime_mode,
        "runtime_descriptor": runtime_descriptor,
        "runtime_executable": runtime_executable,
        "payload_label_count": str(len(payload.get("labels", []))),
        "payload_screen_count": str(len(payload.get("screens", []))),
        "analyzer_version": APP_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    cursor.executemany(
        "INSERT OR REPLACE INTO cache_meta (key, value) VALUES (?, ?)",
        list(meta_entries.items()),
    )


def _persist_labels(conn: sqlite3.Connection, labels: Iterable[Dict[str, Any]], slot_id: int) -> None:
    cursor = conn.cursor()
    for label in labels:
        meta = _strip_keys(label, {"menu_nodes", "outgoing_flows"})
        cursor.execute(
            """
            INSERT INTO labels (
                slot_id, name, file_path, line_number,
                has_dialogue, is_dead_end, flow_complexity, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slot_id,
                label.get("name"),
                label.get("file_path"),
                _safe_int(label.get("line_number")),
                _bool_int(label.get("has_dialogue")),
                _bool_int(label.get("is_dead_end")),
                _safe_int(label.get("flow_complexity")),
                json.dumps(meta, ensure_ascii=False),
            ),
        )
        label_id = cursor.lastrowid

        menus = label.get("menu_nodes") or []
        if menus:
            _persist_menus(cursor, menus, slot_id, label.get("name"))

        flows = label.get("outgoing_flows") or []
        if flows:
            _persist_edges(cursor, flows, slot_id, label.get("name"))


def _persist_menus(
    cursor: sqlite3.Cursor,
    menus: Iterable[Dict[str, Any]],
    slot_id: int,
    label_name: Optional[str],
) -> None:
    for menu in menus:
        metadata = _strip_keys(menu, {"choices"})
        cursor.execute(
            """
            INSERT INTO menus (
                slot_id, label_name, menu_identifier, menu_index, prompt,
                file_path, line_number, is_nested, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slot_id,
                label_name or "",
                menu.get("node_id"),
                _safe_int(menu.get("menu_index")),
                menu.get("prompt"),
                menu.get("file_path"),
                _safe_int(menu.get("line_number")),
                _bool_int(menu.get("is_nested")),
                json.dumps(metadata, ensure_ascii=False),
            ),
        )
        menu_id = cursor.lastrowid
        _persist_menu_choices(cursor, menu.get("choices") or [], slot_id, menu_id)


def _persist_menu_choices(
    cursor: sqlite3.Cursor,
    choices: Iterable[Dict[str, Any]],
    slot_id: int,
    menu_id: int,
) -> None:
    for idx, choice in enumerate(choices):
        metadata = _strip_keys(choice, set())
        cursor.execute(
            """
            INSERT INTO menu_choices (
                slot_id, menu_id, choice_index, text, destination,
                all_destinations, file_path, line_number, has_condition,
                leads_to_label, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slot_id,
                menu_id,
                idx,
                choice.get("text"),
                choice.get("destination"),
                json.dumps(choice.get("all_destinations"), ensure_ascii=False),
                choice.get("file_path"),
                _safe_int(choice.get("line_number")),
                _bool_int(choice.get("has_condition")),
                _bool_int(choice.get("leads_to_label")),
                json.dumps(metadata, ensure_ascii=False),
            ),
        )


def _persist_edges(
    cursor: sqlite3.Cursor,
    flows: Iterable[Dict[str, Any]],
    slot_id: int,
    source_label: Optional[str],
) -> None:
    for flow in flows:
        cursor.execute(
            """
            INSERT INTO edges (
                slot_id, source_label, target_label, flow_type,
                file_path, line_number, condition, context
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slot_id,
                source_label or "",
                flow.get("target_label"),
                flow.get("flow_type"),
                flow.get("file_path"),
                _safe_int(flow.get("line_number")),
                flow.get("condition"),
                flow.get("context"),
            ),
        )


def _persist_screens(
    conn: sqlite3.Connection,
    screens: Iterable[Dict[str, Any]],
    slot_id: int,
) -> None:
    cursor = conn.cursor()
    for screen in screens:
        cursor.execute(
            """
            INSERT INTO screens (
                slot_id, screen_name, screen_type,
                file_path, line_number, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                slot_id,
                screen.get("screen_name"),
                screen.get("screen_type"),
                screen.get("file_path"),
                _safe_int(screen.get("line_number")),
                json.dumps(screen, ensure_ascii=False),
            ),
        )


def _strip_keys(payload: Dict[str, Any], keys: Iterable[str]) -> Dict[str, Any]:
    keys_set = set(keys)
    return {key: value for key, value in payload.items() if key not in keys_set}


def _bool_int(value: Any) -> int:
    return int(bool(value))


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

