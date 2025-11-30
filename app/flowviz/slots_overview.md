# FlowViz Slots Architecture

This document captures the current state of the Ren'Py options "slots" feature, which now underpins FlowViz’s metadata ingestion workflow. It covers both the backend persistence layer and the frontend behavior inside the Source Analysis tab.

---

## 1. User Workflow (Frontend)

| Step | Description                                                  | Key UI Elements                                                                                                                                                 |
| ---- | ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | User opens **Source Analysis → Ren'Py Options** for a story. | Tabbed view inside `SourceAnalysisTab`.                                                                                                                         |
| 2    | User adds a slot via **Add Slot** or clones an existing one. | Modal dialog defined in `SlotModal`.                                                                                                                            |
| 3    | Source type selection                                        | Directory or compressed file (currently ZIP). Drag & drop supported.                                                                                            |
| 4    | Confirmation & copy/extraction                               | QFileDialog and drag events gather input; `SlotModal` asks for confirmation before copying/extracting.                                                          |
| 5    | Visual listing                                               | Each slot pill shows: slot number, source type badge, tag chips (intact/unren/URM), path, added timestamp, reorder arrows, edit/clone/delete, and tag “+” menu. |
| 6    | Tagging                                                      | The plus button opens a menu of fixed tags. Tag chips can be removed inline.                                                                                    |

### Frontend Implementation Notes

- **UI file**: `app/views/renpy_options_tab.py`.
- **Widgets**:
  - `SlotItemWidget` renders each pill and emits signals for edit/clone/delete/tag actions.
  - `SlotModal` handles directory vs ZIP selection, validations, and previews.
  - `SlotDropArea` provides a reusable drag-and-drop frame.
- **Dialogs & Menus**:
  - QFileDialog is used for browsing directories or archives.
  - `QMenu` powers the tag picker (`intact`, `unren`, `URM`).
- **Copying/Extraction**:
  - Directories are copied with a progress dialog via `_copy_directory_slot`.
  - ZIP files are extracted to a temp directory, validated for Ren’Py structure (`game`, `renpy`, `lib`), then moved into the target slot folder (`_extract_zip_slot`).
- **Cloning**:
  - Clones reuse `_copy_directory_slot` against the source slot folder and duplicate tags/metadata.
- **Reordering**:
  - Move up/down buttons swap entries in the in-memory list; persistence of slot numbers is handled by the backend helper `update_story_slot_numbers` when we wire that in for FlowViz ordering needs.

---

## 2. Persistence Layer (Backend)

### Database Schema

Stored in SQLite (`app/db_sqlite.py`) with a dedicated `story_slots` table:

```sql
CREATE TABLE IF NOT EXISTS story_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER NOT NULL,
    slot_number INTEGER NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('directory', 'compressed')),
    destination_path TEXT NOT NULL,
    original_source_path TEXT,
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (story_id) REFERENCES stories (id) ON DELETE CASCADE,
    UNIQUE (story_id, slot_number)
);
```

- **slot_number**: sequential and never reused; new slots use `max(existing)+1`.
- **source_type**: enum enforced at DB level.
- **destination_path**: canonical path under `<story>/slots/<n>`.
- **metadata_json**: currently `{ "tags": ["intact"] }`, ready for future attributes (version info, flags, etc.).

### CRUD Helpers

`db_sqlite.py` exposes:

- `create_story_slot`
- `get_story_slots` / `get_story_slot`
- `update_story_slot_record`
- `delete_story_slot`
- `update_story_slot_numbers` (reserved for future reordering persistence)

All helpers auto-update `updated_at`.

### Loading Pipeline

1. `RenpyOptionsTab.set_story` loads slots via `_load_slots_from_db`.
2. Each DB row is transformed into a `RenpySlot` dataclass (`slot_number`, `paths`, `source_type`, `tags`, `date_added`).
3. UI list caches per-story slots in `self.story_slots` for quick refreshes without re-querying.

### Writing Pipeline

- **Add/Clone**: After copying/extraction succeeds, `create_story_slot` writes the row. The UI reads the row back to sync DB IDs and timestamps.
- **Edit**: Updates `source_type`, `destination_path`, `original_source_path`, and `metadata_json`.
- **Delete**: `delete_story_slot` removes the row; the UI currently leaves filesystem cleanup manual.
- **Tags**: `_persist_slot_metadata` serializes tags to JSON and calls `update_story_slot_record`.

---

## 3. Filesystem Layout

```
<story folder>/
 └── slots/
      ├── 1/  # directory or extracted ZIP contents
      ├── 2/
      └── ...
```

- Slots cloned from directories are copied directly.
- ZIP-based slots extract to a temp dir, validate Ren’Py root structure, then move into `<story>/slots/<n>`.
- Reordering does not rename folders; numbering is tied to creation order to preserve downstream references (hashing, FlowViz links).

---

## 4. FlowViz Integration Points

1. **SDK Extraction**: Each slot is a self-contained working copy. When we run the Ren'Py SDK or FlowViz analyzers, they operate on `destination_path`.
2. **Metadata Cache**: FlowViz can persist AST artifacts (JSON/SQLite/Parquet) alongside the slot directory or in story-specific storage keyed by slot ID.
3. **Tag Semantics**:
   - `intact`: untouched, original assets.
   - `unren`: pass through UnRen wrappers (decompile assets).
   - `URM`: user-defined modifications (e.g., UnRen Modded).
   - Future tags (e.g., `version: 0.54b`) can extend the metadata object without schema changes.
4. **Cross-Feature Consumption**:
   - Dialog Search / Decision Points can read SDK caches per slot to refine lookups.
   - FlowViz UI can filter slots by tag (e.g., show only `intact` builds for baseline graphs).

---

## 5. Next Steps

- **Version tags**: extend metadata schema to support key/value tags (e.g., `version: 0.54b`).
- **Slot status**: add computed badges (e.g., parsed, needs refresh).
- **Bulk operations**: scriptable slot creation (CLI) for batch imports.
- **FlowViz wiring**: integrate slot selection into FlowViz tab so visualizations run against the chosen slot’s cached metadata.
- **Filesystem cleanup**: optional delete/repair actions when source folders go missing.

---

The slots system is now the backbone for FlowViz ingestion—every story can host multiple game states (original, decrypted, modded) with consistent metadata, clear UI cues, and centralized persistence. As FlowViz matures, we can layer versioning, validation, and metadata audits on top of this foundation.
