## Slot Metadata Cache – Implementation Plan

This document expands on `app/flowviz/slot_metadata_cache_requirements.md` and captures a concrete plan for transforming slot contents into FlowViz-ready caches.

### 1. Current Foundations Audit

1. **Slot management UX**
   - `RenpyOptionsTab` renders and manages slots through widgets such as `SlotItemWidget`, `SlotModal`, and `SlotDropArea`, allowing directory/ZIP ingestion, cloning, tagging, reordering, and DB persistence via `db_sqlite` helpers (`create_story_slot`, `update_story_slot_record`, etc.).  
   - The UI enforces the filesystem layout (`<story>/slots/<n>/`) and keeps slot metadata (tags, timestamps) synchronized with SQLite records; drag-and-drop plus dialogs cover both directory and archive import paths.
2. **Backend persistence**
   - `story_slots` table (see `slots_overview.md`) already stores slot number, source type, destination/original paths, and JSON metadata (tags), giving us authoritative IDs we can reference from the cache schema.
3. **FlowViz POC learnings**
   - The POC stack (`flowviz_poc_overview.md`) wires `RenpyFlowDataAdapter` → `SDKFlowGraphBuilder` → SDK workers, then feeds data into the Authoritative Hierarchy System (AHS) before visualization.
   - `ideas-lab/flow-visualizer-poc/renpy_sdk_tests_nov/inspect_label_node.py` demonstrates: a) loading `flowviz_config.json` for per-file `.rpy`/`.rpyc` overrides; b) forcibly hiding source files to trigger `.rpyc` usage; c) registering Ren’Py commands for introspection; d) emitting JSON with preview statements. These behaviors inform the upcoming analyzer CLI and source-mode flags.

### 2. Cache Data Model & Storage Strategy

1. **Authoritative store**
   - One SQLite database per slot at `slots/<slot_number>/cache/metadata.db`, written via temp-file swap to preserve atomicity.
   - Directory should also contain log files (e.g., `extract.log`) tied to each analyzer run.
2. **Proposed tables**
   - `cache_meta(id INTEGER PRIMARY KEY, slot_id INTEGER, story_id INTEGER, schema_version TEXT, analyzer_version TEXT, sdk_mode TEXT, source_mode TEXT, created_at TEXT, bundled_runtime_used INTEGER, notes TEXT)`
   - `labels(id INTEGER PRIMARY KEY, slot_id INTEGER, name TEXT, location TEXT, hash TEXT, entrypoint INTEGER, metadata_json TEXT)`
   - `menus(id INTEGER PRIMARY KEY, slot_id INTEGER, parent_label_id INTEGER, guard_expr TEXT, location TEXT, metadata_json TEXT)`
   - `menu_choices(id INTEGER PRIMARY KEY, menu_id INTEGER, text TEXT, destination_kind TEXT, destination_ref TEXT, block_json TEXT, display_conditions TEXT)`
   - `edges(id INTEGER PRIMARY KEY, slot_id INTEGER, source_kind TEXT, source_ref TEXT, target_kind TEXT, target_ref TEXT, edge_type TEXT, metadata_json TEXT)`
   - `screens(id INTEGER PRIMARY KEY, slot_id INTEGER, name TEXT, location TEXT, actionable_json TEXT, metadata_json TEXT)`
   - `screen_actions(id INTEGER PRIMARY KEY, screen_id INTEGER, action_type TEXT, target TEXT, metadata_json TEXT)` (optional extension for actionable items)
3. **Provenance rules**
   - Cache writes must record: story/slot ID, source selection (`rpyc_only`, `rpy_only`, `auto`), list of files forced to `.rpyc`, SDK vs bundled runtime path, analyzer version hash, and timestamp.
   - Analyzer writes to `metadata.tmp`, validates integrity, then replaces `metadata.db`. Failed runs delete the temp file and leave the previous cache intact.
4. **JSON support**
   - Use SQLite JSON for flexible fields (`metadata_json`, `block_json`, `actionable_json`), enabling future additions (e.g., scene statements) without schema churn.

### 3. Extraction Pipeline Design

1. **Control flow**
   - `flowviz-cache` CLI (PowerShell-friendly) accepts `--story-id`, `--slot-id`, `--source-mode`, `--use-bundled-runtime`, and optional config file path (default: slot root `flowviz_config.json`).
   - Steps:
     1. Resolve slot record from SQLite (`story_slots`), verify destination path exists, and ensure cache folder exists.
     2. Load configuration: global source mode + per-file overrides (`ignore_files`, `force_rpyc_files`, `force_source_files`).
     3. Select runtime (bundled vs default; see section 4).
     4. Launch SDK worker (Py2 or Py3) with environment variables describing source mode, forced files, and log paths.
     5. Worker traverses AST (labels, menus, choices, screens, jumps/calls) and emits structured JSON via stdout/pipe.
     6. Host process streams/validates payload, normalizes it into the SQLite schema, and writes provenance rows.
     7. Write logs, finalize cache swap, and emit summary to console.
2. **Source selection enforcement**
   - `--source-mode=rpyc_only` hides `.rpy` files (as in POC) before bootstrap; `rpy_only` hides `.rpyc`; `auto` leaves both but still honors per-file overrides.
   - Overrides allow explicit lists of `.rpyc` to force even when `.rpy` exists; these lists propagate to the worker in JSON config.
3. **Error strategy**
   - Any Ren’Py bootstrap or worker exception aborts the run, logs context (slot, runtime path, label currently processed), and cleans up temp database.
   - Partial data is never persisted; analyzer exits non-zero and indicates user action (e.g., inspect log file).

### 4. Runtime & Worker Strategy

1. **Runtime detection order**
   - Attempt to locate bundled runtime inside the slot (`slots/<n>/renpy/`, `lib/py*-*`), mirroring the POC’s `runtime_locator.py`.
   - If found, derive interpreter version (2.x vs 3.x) and select the matching worker script (`sdk_flow_builder_worker.py` vs `_py2`).
   - If bundled detection fails or worker exits with incompatibility, fall back to the embedded SDK at `app/renpy-source-api/renpy_sdk/renpy-8.4.0-sdk`.
2. **Packaging**
   - Both workers must be packaged with the analyzer, and the CLI should expose explicit flags: `--bundled-runtime=prefer|require|disable` to control fallback.
   - Document environment variable expectations (e.g., `FLOW_BUNDLED_RENPY_BASE`, `FLOW_PYTHON_STDLIB`) so future features can introspect runtime provenance from `cache_meta`.
3. **Compatibility logging**
   - Cache metadata should record which runtime actually executed, along with worker version string, so downstream consumers can correlate discrepancies.

### 5. Tooling & Diagnostics Suite

1. **Slot Analyzer CLI**
   - Entry: `python run.py flowviz-cache --slot <id> [options]`.
   - Outputs summary metrics (counts of labels/menus/screens) and writes logs + SQLite cache.
2. **Label/Menu Inspector**
   - Entry: `python run.py flowviz-cache inspect --slot <id> --label start`.
   - Reads from cache, dumps JSON showing outgoing edges, menu choices, nested menus—useful to verify hashing and metadata fidelity without rerunning SDK.
3. **Cache Validator**
   - Entry: `python run.py flowviz-cache validate --slot <id>`.
   - Checks schema version, required tables, FK constraints, and ensures provenance matches current analyzer version; warns if cache predates slot modification timestamp (if tracked).
4. **BOM/Encoding Tester**
   - Entry: `python run.py flowviz-cache encoding-test --slot <id> --file game/script.rpy`.
   - Ensures problematic files (e.g., BOM variations) can be opened; surfaces encoding exceptions before full extraction.
5. **AST Chunk Dumper**
   - Entry: `python run.py flowviz-cache dump-ast --slot <id> --label start --raw`.
   - Invokes worker in a stripped-down mode (or reads cached raw JSON if we persist it) to compare SDK output with normalized rows—critical for debugging mismatches.
6. **Logging artifacts**
   - All tools share the logging infrastructure (dual console/file handlers) and store detailed logs alongside the cache folder for quick inspection.

### 6. Operational Guidelines & Open Questions

1. **Performance stance**
   - Prioritize correctness and completeness; multi-minute runs are acceptable because caches avoid repeated SDK executions.
2. **Logging expectations**
   - Structured logging plus high-level console prints; include slot/story IDs, runtime paths, and label/menu identifiers. Logs should be UTF-8 and Windows-friendly.
3. **Open questions to resolve during implementation**
   - Schema fidelity vs. AHS alignment (how much normalization occurs at cache stage).
   - Automatic staleness detection strategy (hashing slot files vs. manual re-run).
   - Runtime/memory guardrails for analyzer runs.
   - Which inspectors are mandatory for MVP vs. deferred follow-ups.
   - Cache size/security policies (max DB size, sanitization for exports).
   - Bundled runtime packaging details (distribution, updates, fallbacks) beyond the outline above.
   - Preferred log file format (plain text vs structured JSON) for per-slot artifacts.


