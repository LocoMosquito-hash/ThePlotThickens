"""Utilities to inspect, validate, and export slot cache databases."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


def run_cache_inspector(args) -> int:
    """Entry point for `flowviz-cache-inspect`."""

    project_root = Path(__file__).resolve().parents[2]
    cache_db = _resolve_cache_db(project_root, args.slot_id)
    if cache_db is None:
        print(f"[inspect] metadata.db not found for slot {args.slot_id}")
        return 1

    with sqlite3.connect(cache_db) as conn:
        conn.row_factory = sqlite3.Row
        if getattr(args, "label", None):
            return _inspect_label(conn, args.label)
        if getattr(args, "screen", None):
            return _inspect_screen(conn, args.screen)
        return _print_cache_summary(conn, label_limit=args.limit, screen_limit=args.screen_limit)


def run_cache_validator(args) -> int:
    """Entry point for `flowviz-cache-validate`."""

    project_root = Path(__file__).resolve().parents[2]
    cache_db = _resolve_cache_db(project_root, args.slot_id)
    if cache_db is None:
        print(f"[validate] metadata.db not found for slot {args.slot_id}")
        return 1

    issues: List[str] = []
    with sqlite3.connect(cache_db) as conn:
        issues.extend(_validate_required_tables(conn))
        issues.extend(_validate_cache_meta(conn))
        issues.extend(_validate_menu_references(conn))

    if issues:
        print("Cache validation FAILED with the following issues:")
        for idx, issue in enumerate(issues, 1):
            print(f" {idx}. {issue}")
        return 1

    print("Cache validation succeeded: no blocking issues detected.")
    return 0


def run_cache_export(args) -> int:
    """Entry point for `flowviz-cache-export`."""

    project_root = Path(__file__).resolve().parents[2]
    cache_db = _resolve_cache_db(project_root, args.slot_id)
    if cache_db is None:
        print(f"[export] metadata.db not found for slot {args.slot_id}")
        return 1

    output_path = (
        Path(args.output).expanduser()
        if getattr(args, "output", None)
        else Path(cache_db).parent / "graph_export.json"
    )

    with sqlite3.connect(cache_db) as conn:
        conn.row_factory = sqlite3.Row
        export_data = _build_graph_export(conn)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(export_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[export] Graph data written to {output_path}")
    return 0


def _resolve_cache_db(project_root: Path, slot_id: int) -> Optional[Path]:
    db_path = project_root / "the_plot_thickens.db"
    if not db_path.exists():
        print(f"[inspect] main database not found at {db_path}")
        return None

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT destination_path FROM story_slots WHERE id = ?",
            (slot_id,),
        )
        row = cursor.fetchone()
        if not row:
            print(f"[inspect] slot id {slot_id} not found.")
            return None
        slot_path = Path(row[0]).expanduser().resolve()

    cache_db = slot_path / "cache" / "metadata.db"
    if not cache_db.exists():
        return None
    return cache_db


def _print_cache_summary(
    conn: sqlite3.Connection,
    *,
    label_limit: int,
    screen_limit: int,
) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM cache_meta WHERE key='story_title'")
    story_title = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM labels")
    label_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM menus")
    menu_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM screens")
    screen_count = cursor.fetchone()[0]

    print("FlowViz cache summary")
    print(f" Story: {story_title[0] if story_title else '<unknown>'}")
    print(f" Labels: {label_count}")
    print(f" Menus: {menu_count}")
    print(f" Screens: {screen_count}")

    cursor.execute(
        "SELECT name, file_path, line_number FROM labels ORDER BY name LIMIT ?",
        (label_limit,),
    )
    rows = cursor.fetchall()
    if rows:
        print(f"\nFirst {len(rows)} labels:")
        for name, file_path, line in rows:
            print(f" - {name} ({file_path}:{line})")

    cursor.execute(
        "SELECT screen_name, file_path, line_number FROM screens ORDER BY screen_name LIMIT ?",
        (screen_limit,),
    )
    screens = cursor.fetchall()
    if screens:
        print(f"\nFirst {len(screens)} screens:")
        for name, file_path, line in screens:
            print(f" - {name} ({file_path}:{line})")
    return 0


def _inspect_label(conn: sqlite3.Connection, label_name: str) -> int:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, file_path, line_number, metadata_json FROM labels WHERE name = ?",
        (label_name,),
    )
    label_row = cursor.fetchone()
    if not label_row:
        print(f"[inspect] Label '{label_name}' not found in cache.")
        return 1

    label_id = label_row[0]
    print(f"Label: {label_name}")
    print(f" File: {label_row[1]}:{label_row[2]}")
    print(" Menus:")
    slot_id = _get_meta_value(conn, "slot_id")
    cursor.execute(
        "SELECT id, menu_index, prompt FROM menus WHERE slot_id = ? AND label_name = ?",
        (slot_id, label_name),
    )
    menus = cursor.fetchall()
    if not menus:
        print("  (none)")
    for menu_row in menus:
        menu_id = menu_row[0]
        print(f"  • Menu idx {menu_row[1]} – prompt: {menu_row[2]!r}")
        cursor.execute(
            """
            SELECT choice_index, text, destination, has_condition
            FROM menu_choices WHERE menu_id = ?
            ORDER BY choice_index
            """,
            (menu_id,),
        )
        choices = cursor.fetchall()
        for choice in choices:
            print(
                f"     - [{choice[0]}] {choice[1]!r} -> {choice[2] or '<return>'}"
                f"{' (condition)' if choice[3] else ''}"
            )

    print(" Outgoing flows:")
    cursor.execute(
        """
        SELECT target_label, flow_type, condition
        FROM edges
        WHERE source_label = ?
        """,
        (label_name,),
    )
    edges = cursor.fetchall()
    if not edges:
        print("  (none)")
    for edge in edges:
        condition = f" if {edge[2]}" if edge[2] else ""
        print(f"  -> {edge[0] or '<return>'} [{edge[1]}]{condition}")
    return 0


def _inspect_screen(conn: sqlite3.Connection, screen_name: str) -> int:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT screen_name, file_path, line_number, metadata_json
        FROM screens
        WHERE screen_name = ?
        """,
        (screen_name,),
    )
    row = cursor.fetchone()
    if not row:
        print(f"[inspect] Screen '{screen_name}' not found in cache.")
        return 1

    print(f"Screen: {row[0]}")
    print(f" File: {row[1]}:{row[2]}")
    metadata = _parse_json(row[3])
    elements = metadata.get("elements", [])
    if not elements:
        print(" Elements: (none)")
        return 0

    print(" Elements:")
    for idx, element in enumerate(elements):
        text = element.get("text") or ""
        coordinates = element.get("coordinates")
        actions = element.get("actions") or []
        print(f"  • Element {idx} text={text!r} coords={coordinates or '-'}")
        for action in actions:
            action_type = action.get("action_type") or action.get("type")
            destination = action.get("destination") or action.get("target_label") or action.get("target_screen")
            condition = action.get("condition")
            print(
                f"     - action={action_type} target={destination or '<none>'}"
                f"{' if ' + condition if condition else ''}"
            )
    return 0


def _validate_required_tables(conn: sqlite3.Connection) -> List[str]:
    """Ensure the core tables exist."""

    required = {"cache_meta", "labels", "menus", "menu_choices", "edges", "screens"}
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ({placeholders})".format(
            placeholders=",".join("?" for _ in required)
        ),
        tuple(required),
    )
    existing = {row[0] for row in cursor.fetchall()}
    missing = required - existing
    return [f"Missing required table '{name}'." for name in sorted(missing)]


def _validate_cache_meta(conn: sqlite3.Connection) -> List[str]:
    cursor = conn.execute(
        "SELECT key, value FROM cache_meta WHERE key IN ('story_id', 'slot_id', 'generated_at')"
    )
    meta = {row[0]: row[1] for row in cursor.fetchall()}
    issues: List[str] = []
    for key in ("story_id", "slot_id", "generated_at"):
        if key not in meta:
            issues.append(f"cache_meta missing '{key}'.")
    return issues


def _validate_menu_references(conn: sqlite3.Connection) -> List[str]:
    """Check for menus without choices and choices pointing to missing menus."""

    issues: List[str] = []
    cursor = conn.execute(
        """
        SELECT menus.id
        FROM menus
        LEFT JOIN menu_choices ON menu_choices.menu_id = menus.id
        GROUP BY menus.id
        HAVING COUNT(menu_choices.id) = 0
        """
    )
    empty = cursor.fetchall()
    if empty:
        issues.append(f"{len(empty)} menus have zero choices.")

    cursor = conn.execute(
        """
        SELECT menu_choices.id
        FROM menu_choices
        LEFT JOIN menus ON menu_choices.menu_id = menus.id
        WHERE menus.id IS NULL
        """
    )
    orphans = cursor.fetchall()
    if orphans:
        issues.append(f"{len(orphans)} menu choices reference missing menus.")
    return issues


def _build_graph_export(conn: sqlite3.Connection) -> Dict[str, Any]:
    metadata = {row["key"]: row["value"] for row in conn.execute("SELECT key, value FROM cache_meta")}
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    label_nodes: Dict[str, str] = {}
    for row in conn.execute("SELECT name, file_path, line_number FROM labels"):
        node_id = f"label:{row['name']}"
        label_nodes[row["name"]] = node_id
        nodes.append(
            {
                "id": node_id,
                "type": "label",
                "name": row["name"],
                "file_path": row["file_path"],
                "line_number": row["line_number"],
            }
        )

    menu_nodes: Dict[int, str] = {}
    for row in conn.execute("SELECT id, label_name, menu_index, prompt FROM menus"):
        node_id = f"menu:{row['id']}"
        menu_nodes[row["id"]] = node_id
        nodes.append(
            {
                "id": node_id,
                "type": "menu",
                "label_name": row["label_name"],
                "menu_index": row["menu_index"],
                "prompt": row["prompt"],
            }
        )
        source_id = label_nodes.get(row["label_name"])
        if source_id:
            edges.append(
                {
                    "id": f"edge:{source_id}->{node_id}",
                    "kind": "label-menu",
                    "source": source_id,
                    "target": node_id,
                }
            )

    for row in conn.execute(
        """
        SELECT menu_choices.menu_id, menu_choices.choice_index, menu_choices.text,
               menu_choices.destination, menu_choices.has_condition
        FROM menu_choices
        """
    ):
        menu_node_id = menu_nodes.get(row["menu_id"])
        if not menu_node_id:
            continue
        target_label = row["destination"]
        target_node = label_nodes.get(target_label) if target_label else None
        edges.append(
            {
                "id": f"choice:{row['menu_id']}:{row['choice_index']}",
                "kind": "menu-choice",
                "source": menu_node_id,
                "target": target_node or f"label:{target_label}" if target_label else "<return>",
                "text": row["text"],
                "condition": bool(row["has_condition"]),
            }
        )

    for row in conn.execute(
        "SELECT source_label, target_label, flow_type, condition FROM edges"
    ):
        source_id = label_nodes.get(row["source_label"])
        target_id = label_nodes.get(row["target_label"]) if row["target_label"] else "<return>"
        if not source_id:
            continue
        edges.append(
            {
                "id": f"flow:{row['source_label']}->{row['target_label'] or 'return'}",
                "kind": "label-flow",
                "source": source_id,
                "target": target_id,
                "flow_type": row["flow_type"],
                "condition": row["condition"],
            }
        )

    for row in conn.execute("SELECT screen_name, file_path, line_number, metadata_json FROM screens"):
        node_id = f"screen:{row['screen_name']}"
        nodes.append(
            {
                "id": node_id,
                "type": "screen",
                "name": row["screen_name"],
                "file_path": row["file_path"],
                "line_number": row["line_number"],
            }
        )
        metadata_json = _parse_json(row["metadata_json"])
        for element in metadata_json.get("elements", []):
            for action in element.get("actions", []):
                destination = (
                    action.get("destination")
                    or action.get("target_label")
                    or action.get("target_screen")
                )
                if not destination:
                    continue
                target_id = (
                    label_nodes.get(destination)
                    or f"label:{destination}"
                )
                edges.append(
                    {
                        "id": f"screen:{row['screen_name']}->{destination}",
                        "kind": "screen-action",
                        "source": node_id,
                        "target": target_id,
                        "action_type": action.get("action_type") or action.get("type"),
                    }
                )

    return {"metadata": metadata, "nodes": nodes, "edges": edges}


def _get_meta_value(conn: sqlite3.Connection, key: str) -> Optional[str]:
    cursor = conn.execute("SELECT value FROM cache_meta WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row[0] if row else None


def _parse_json(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}

