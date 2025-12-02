"""Helpers to persist FlowViz SDK payloads into per-slot cache databases."""

from __future__ import annotations

import hashlib
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

        label_hashes: Dict[str, str] = {}
        menu_hashes: Dict[int, str] = {}
        ahs_nodes: Dict[str, Dict[str, Any]] = {}
        ahs_edges: List[Dict[str, Any]] = []

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
        _persist_labels(
            conn,
            payload.get("labels", []),
            slot_record["id"],
            label_hashes,
            menu_hashes,
            ahs_nodes,
            ahs_edges,
        )
        _persist_screens(
            conn,
            payload.get("screens", []),
            slot_record["id"],
            label_hashes,
            ahs_nodes,
            ahs_edges,
        )
        _persist_ahs_core(conn, ahs_nodes, ahs_edges)
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
            node_hash TEXT,
            parent_hash TEXT,
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
            node_hash TEXT,
            parent_hash TEXT,
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
            target_hash TEXT,
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
            context TEXT,
            source_hash TEXT,
            target_hash TEXT
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
            node_hash TEXT,
            parent_hash TEXT,
            metadata_json TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ahs_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER NOT NULL,
            node_hash TEXT NOT NULL UNIQUE,
            node_type TEXT NOT NULL,
            parent_hash TEXT,
            label_name TEXT,
            menu_id INTEGER,
            screen_name TEXT,
            helper_flag INTEGER DEFAULT 0,
            metadata_json TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ahs_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER NOT NULL,
            source_hash TEXT NOT NULL,
            target_hash TEXT,
            edge_kind TEXT NOT NULL,
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


def _persist_labels(
    conn: sqlite3.Connection,
    labels: Iterable[Dict[str, Any]],
    slot_id: int,
    label_hashes: Dict[str, str],
    menu_hashes: Dict[int, str],
    ahs_nodes: Dict[str, Dict[str, Any]],
    ahs_edges: List[Dict[str, Any]],
) -> None:
    cursor = conn.cursor()
    for label in labels:
        meta = _strip_keys(label, {"menu_nodes", "outgoing_flows"})
        label_name = label.get("name") or ""
        node_hash = _generate_hash(
            "label",
            slot_id,
            label_name,
            label.get("file_path") or "",
            _safe_int(label.get("line_number")),
        )
        label_hashes[label_name] = node_hash
        cursor.execute(
            """
            INSERT INTO labels (
                slot_id, name, file_path, line_number,
                has_dialogue, is_dead_end, flow_complexity,
                node_hash, parent_hash, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slot_id,
                label_name,
                label.get("file_path"),
                _safe_int(label.get("line_number")),
                _bool_int(label.get("has_dialogue")),
                _bool_int(label.get("is_dead_end")),
                _safe_int(label.get("flow_complexity")),
                node_hash,
                None,
                json.dumps(meta, ensure_ascii=False),
            ),
        )

        _register_ahs_node(
            ahs_nodes,
            slot_id=slot_id,
            node_hash=node_hash,
            node_type="label",
            display_name=label_name,
            parent_hash=None,
            metadata={
                "file_path": label.get("file_path"),
                "line_number": _safe_int(label.get("line_number")),
            },
        )

        menus = label.get("menu_nodes") or []
        if menus:
            _persist_menus(
                cursor,
                menus,
                slot_id,
                label_name,
                node_hash,
                menu_hashes,
                ahs_nodes,
                ahs_edges,
                label_hashes,
            )

        flows = label.get("outgoing_flows") or []
        if flows:
            _persist_edges(
                cursor,
                flows,
                slot_id,
                label_name,
                node_hash,
                label_hashes,
                ahs_edges,
            )


def _persist_menus(
    cursor: sqlite3.Cursor,
    menus: Iterable[Dict[str, Any]],
    slot_id: int,
    label_name: Optional[str],
    parent_hash: Optional[str],
    menu_hashes: Dict[int, str],
    ahs_nodes: Dict[str, Dict[str, Any]],
    ahs_edges: List[Dict[str, Any]],
    label_hashes: Dict[str, str],
) -> None:
    for menu in menus:
        metadata = _strip_keys(menu, {"choices"})
        node_hash = _generate_hash(
            "menu",
            slot_id,
            label_name or "",
            menu.get("node_id") or "",
            _safe_int(menu.get("menu_index")),
            menu.get("prompt") or "",
        )
        cursor.execute(
            """
            INSERT INTO menus (
                slot_id, label_name, menu_identifier, menu_index, prompt,
                file_path, line_number, is_nested, node_hash, parent_hash, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                node_hash,
                parent_hash,
                json.dumps(metadata, ensure_ascii=False),
            ),
        )
        menu_id = cursor.lastrowid
        menu_hashes[menu_id] = node_hash

        menu_entry = _register_ahs_node(
            ahs_nodes,
            slot_id=slot_id,
            node_hash=node_hash,
            node_type="menu",
            display_name=f"{label_name or ''}:{menu.get('menu_index')}",
            parent_hash=parent_hash,
            metadata={
                "prompt": menu.get("prompt"),
                "menu_identifier": menu.get("node_id"),
            },
        )

        menu_entry["menu_id"] = menu_id
        if parent_hash:
            _register_ahs_edge(
                ahs_edges,
                slot_id=slot_id,
                source_hash=parent_hash,
                target_hash=node_hash,
                edge_kind="label-menu",
                metadata={},
            )

        _persist_menu_choices(
            cursor,
            menu.get("choices") or [],
            slot_id,
            menu_id,
            node_hash,
            label_hashes,
            ahs_edges,
        )


def _persist_menu_choices(
    cursor: sqlite3.Cursor,
    choices: Iterable[Dict[str, Any]],
    slot_id: int,
    menu_id: int,
    menu_hash: str,
    label_hashes: Dict[str, str],
    ahs_edges: List[Dict[str, Any]],
) -> None:
    for idx, choice in enumerate(choices):
        metadata = _strip_keys(choice, set())
        destination = choice.get("destination")
        target_hash = label_hashes.get(destination) if destination else None
        cursor.execute(
            """
            INSERT INTO menu_choices (
                slot_id, menu_id, choice_index, text, destination,
                all_destinations, file_path, line_number, has_condition,
                leads_to_label, target_hash, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slot_id,
                menu_id,
                idx,
                choice.get("text"),
                destination,
                json.dumps(choice.get("all_destinations"), ensure_ascii=False),
                choice.get("file_path"),
                _safe_int(choice.get("line_number")),
                _bool_int(choice.get("has_condition")),
                _bool_int(choice.get("leads_to_label")),
                target_hash,
                json.dumps(metadata, ensure_ascii=False),
            ),
        )
        _register_ahs_edge(
            ahs_edges,
            slot_id=slot_id,
            source_hash=menu_hash,
            target_hash=target_hash,
            edge_kind="menu-choice",
            metadata={
                "choice_index": idx,
                "text": choice.get("text"),
                "leads_to_label": bool(choice.get("leads_to_label")),
            },
        )


def _persist_edges(
    cursor: sqlite3.Cursor,
    flows: Iterable[Dict[str, Any]],
    slot_id: int,
    source_label: Optional[str],
    source_hash: Optional[str],
    label_hashes: Dict[str, str],
    ahs_edges: List[Dict[str, Any]],
) -> None:
    for flow in flows:
        target_hash = label_hashes.get(flow.get("target_label"))
        cursor.execute(
            """
            INSERT INTO edges (
                slot_id, source_label, target_label, flow_type,
                file_path, line_number, condition, context,
                source_hash, target_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                source_hash,
                target_hash,
            ),
        )
        if source_hash:
            _register_ahs_edge(
                ahs_edges,
                slot_id=slot_id,
                source_hash=source_hash,
                target_hash=target_hash,
                edge_kind="label-flow",
                metadata={
                    "flow_type": flow.get("flow_type"),
                    "condition": flow.get("condition"),
                },
            )


def _persist_screens(
    conn: sqlite3.Connection,
    screens: Iterable[Dict[str, Any]],
    slot_id: int,
    label_hashes: Dict[str, str],
    ahs_nodes: Dict[str, Dict[str, Any]],
    ahs_edges: List[Dict[str, Any]],
) -> None:
    cursor = conn.cursor()
    for screen in screens:
        node_hash = _generate_hash(
            "screen",
            slot_id,
            screen.get("screen_name") or "",
            screen.get("file_path") or "",
            _safe_int(screen.get("line_number")),
        )
        cursor.execute(
            """
            INSERT INTO screens (
                slot_id, screen_name, screen_type,
                file_path, line_number, node_hash, parent_hash, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                slot_id,
                screen.get("screen_name"),
                screen.get("screen_type"),
                screen.get("file_path"),
                _safe_int(screen.get("line_number")),
                node_hash,
                None,
                json.dumps(screen, ensure_ascii=False),
            ),
        )
        screen_entry = _register_ahs_node(
            ahs_nodes,
            slot_id=slot_id,
            node_hash=node_hash,
            node_type="screen",
            display_name=screen.get("screen_name") or "",
            parent_hash=None,
            metadata={
                "file_path": screen.get("file_path"),
                "line_number": _safe_int(screen.get("line_number")),
            },
        )

        screen_entry["screen_name"] = screen.get("screen_name") or ""

        for element in screen.get("elements") or []:
            for action in element.get("actions") or []:
                destination = (
                    action.get("destination")
                    or action.get("target_label")
                    or action.get("target_screen")
                )
                if not destination:
                    continue
                target_hash = label_hashes.get(destination)
                _register_ahs_edge(
                    ahs_edges,
                    slot_id=slot_id,
                    source_hash=node_hash,
                    target_hash=target_hash,
                    edge_kind="screen-action",
                    metadata={
                        "action_type": action.get("action_type") or action.get("type"),
                        "target": destination,
                    },
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


def _generate_hash(*components: Any) -> str:
    normalized = "|".join(str(component) for component in components)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _register_ahs_node(
    ahs_nodes: Dict[str, Dict[str, Any]],
    *,
    slot_id: int,
    node_hash: str,
    node_type: str,
    display_name: str,
    parent_hash: Optional[str],
    metadata: Dict[str, Any],
    helper_flag: int = 0,
) -> Dict[str, Any]:
    if node_hash in ahs_nodes:
        return ahs_nodes[node_hash]
    entry = {
        "slot_id": slot_id,
        "node_hash": node_hash,
        "node_type": node_type,
        "parent_hash": parent_hash,
        "label_name": display_name if node_type == "label" else None,
        "menu_id": None,
        "screen_name": display_name if node_type == "screen" else None,
        "helper_flag": helper_flag,
        "metadata_json": json.dumps(metadata, ensure_ascii=False),
    }
    ahs_nodes[node_hash] = entry
    return entry


def _register_ahs_edge(
    ahs_edges: List[Dict[str, Any]],
    *,
    slot_id: int,
    source_hash: Optional[str],
    target_hash: Optional[str],
    edge_kind: str,
    metadata: Dict[str, Any],
) -> None:
    if not source_hash:
        return
    ahs_edges.append(
        {
            "slot_id": slot_id,
            "source_hash": source_hash,
            "target_hash": target_hash,
            "edge_kind": edge_kind,
            "metadata_json": json.dumps(metadata, ensure_ascii=False),
        }
    )


def _persist_ahs_core(
    conn: sqlite3.Connection,
    ahs_nodes: Dict[str, Dict[str, Any]],
    ahs_edges: List[Dict[str, Any]],
) -> None:
    if not ahs_nodes and not ahs_edges:
        return
    cursor = conn.cursor()
    if ahs_nodes:
        cursor.executemany(
            """
            INSERT OR REPLACE INTO ahs_nodes (
                slot_id, node_hash, node_type, parent_hash,
                label_name, menu_id, screen_name, helper_flag, metadata_json
            )
            VALUES (
                :slot_id, :node_hash, :node_type, :parent_hash,
                :label_name, :menu_id, :screen_name, :helper_flag, :metadata_json
            )
            """,
            ahs_nodes.values(),
        )
    if ahs_edges:
        cursor.executemany(
            """
            INSERT INTO ahs_edges (
                slot_id, source_hash, target_hash, edge_kind, metadata_json
            )
            VALUES (
                :slot_id, :source_hash, :target_hash, :edge_kind, :metadata_json
            )
            """,
            ahs_edges,
        )

