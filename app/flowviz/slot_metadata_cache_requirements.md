## Slot Metadata Cache Requirements Guide

Audience: agentic coding model tasked with delivering a working slot-level metadata cache for FlowViz. This document captures **what** needs to be true before implementation planning begins; it intentionally stops short of a detailed build plan.

### 1. Background & Context

- `app/views/renpy_options_tab.py` already manages slot creation, cloning, and tagging (`slots_overview.md`).
- The FlowViz POC (`flowviz_poc_overview.md`) proves we can drive the Ren’Py SDK workers and normalize graphs via the Authoritative Hierarchy System (AHS).
- `future_flow.md` states the next milestone: run the SDK analyzers against any slot and persist reusable metadata so other tabs stop relying on brittle grep workflows.

### 2. Scope Boundary

- **In scope:** everything required to take a slot’s working copy, extract AST-derived narrative primitives, and persist them into a reusable cache.
- **Out of scope for this phase:** UI integrations (Dialog Search, Decision Points, FlowViz rendering), analytics, or non-narrative metadata (e.g., ATL, widget trees). Those consumers will read the cache later.

### 3. Definition of Done Signals

1. Analyzer can run against any slot and emit a cache without manual edits to the slot itself.
2. Inspecting a cached label exposes accurate outgoing flows (calls, jumps, menus, nested menus, label menus).
3. Inspecting a cached menu exposes the right choices, and each choice resolves to its destination label/menu block.
4. Inspecting a menu choice reveals the statements inside (dialogue, scene calls) so downstream features can map assets later.
5. Inspecting a screen lists actionable items relevant to narrative branching (buttons, screen-level jumps).
6. Re-running the analyzer overwrites the cache cleanly; downstream consumers only read the latest snapshot.

### 4. Functional Requirements

- **Primary pipeline**
  1. Select slot (story id + slot id) → resolve filesystem path.
  2. Launch SDK workers (default or bundled runtime) to traverse AST and return structured payloads.
  3. Normalize payloads into cache-ready tables (labels, menus, menu choices, screens, edges, metadata).
  4. Write cache to `slots/<slot_number>/cache/metadata.db` atomically (replace on success).
- **Narrative focus:** first milestone stores only labels, menus, menu choices, jumps, calls, and screens. Cache schema must leave room for future fields such as `scene` statements or asset references.
- **SDK parsing contract:** all metadata must originate from the official Ren’Py/Python AST pipeline—no regex scrapers or custom parsers. Exceptions (e.g., temporary regex patches) require explicit approval because handcrafted parsers historically regressed constantly compared to SDK output.
- **Source selection modes:** analyzer must expose three flags:
  - `rpyc_only` (default) – process compiled `.rpyc` files exclusively.
  - `rpy_only` – ignore `.rpyc`, use plain-text `.rpy`.
  - `auto` – allow mixed input.
    Per-file/per-directory overrides (as in the POC `flowviz_config.json`) supersede the global mode so specific scripts can force `.rpyc` even in `.rpy` mode (or vice versa). These controls must flow from the UI config down to the worker launch.
- **Cache introspection:** each cache must store provenance (slot id, story id, analyzer version, timestamp, SDK flavor) so stale or incompatible caches can be detected.
- **Error handling:** failures must be logged with actionable context (slot path, SDK command, offending label). Partial caches should be discarded to avoid confusing consumers.

### 5. Data & Storage Requirements

- **Authoritative store:** single SQLite file per slot (`metadata.db`). Reasons:
  - transactional writes when normalizing large AST payloads;
  - indexed queries for downstream consumers (e.g., find all menus referencing a label);
  - easy replacement on re-run.
- **Supporting artifacts (optional but encouraged):**
  - Generated JSON snapshots for targeted inspectors (e.g., one label or menu block) to aid debugging;
  - `cache_meta` table describing schema version, extractor version, timestamps, SDK path, and whether `.rpyc` forcing was enabled.
- **Illustrative schema (subject to planning refinement):**
  - `labels(id, slot_id, name, location, hash, entrypoint_flag, summary_json)`
  - `menus(id, label_id, location, guard_expr, metadata_json)`
  - `menu_choices(id, menu_id, text, destination_type, destination_id, block_json)`
  - `edges(id, source_type, source_id, target_type, target_id, edge_kind)`
  - `screens(id, name, location, actionable_json)`
  - `cache_meta(key, value)`
- **Replace-in-place rule:** analyzer writes to a temp SQLite file and swaps it into `cache/metadata.db` only after success.

### 6. Tooling & Inspectors

- Provide a suite of mini-tools (CLI or callable scripts) to test each stage without launching the full TPT app:
  - **Slot analyzer CLI** (`python run.py flowviz-cache --slot <id>` or similar) to trigger the full pipeline.
  - **Label/menu inspector** (inspired by `ideas-lab/.../inspect_label_node.py`) that reads from the cache, verifies outgoing edges, and produces JSON summaries.
  - **Cache validator** that checks schema version, required tables, and foreign keys; reports if cache is stale/missing.
  - **BOM/encoding tester** to exercise edge-case files (e.g., unusual encodings, mixed newline styles) before running the full analyzer.
  - **AST chunk dumper** to compare raw SDK output vs. normalized tables when debugging mismatches.
- Each tool should be callable from PowerShell (`python run.py <subcommand>`), and—per `future_flow.md`—ideally runnable independently for rapid iteration.

-### 7. Operational Considerations

- **Performance**: early iterations should optimize for correctness, not speed. The cache exists precisely to avoid repeated SDK runs; even multi-minute extractions are acceptable because a single slot run amortizes hours of manual analysis. Planning can revisit runtime/memory guardrails later, but the MVP must bias toward fidelity (handling nested menus, edge cases) over micro-optimizations.
- **Logging**: rely on structured logging while still allowing lightweight `print` output for quick CLI feedback. Console prints should stay high-level; the detailed story lives in log handlers (e.g., `logging` module configured with both console and file handlers per Python best practices). Logs must capture slot id, story id, SDK selection, label/menu names, filesystem paths, and error payloads. Whenever feasible, store the log file alongside `metadata.db` inside `slots/<n>/cache/` so developers can correlate cache contents with extraction traces quickly. Third-party helpers (colorized logs, JSON loggers) can be evaluated during planning.
- **Slot lifecycle**: cache folder (`slots/<n>/cache/`) is owned by the extractor. Deleting a slot must remove its cache; cloning slots should clone caches only if explicitly requested (decision deferred to planning).
- **Standalone runs**: components should be launchable without the full GUI to support iterative debugging, as emphasized in `future_flow.md`.
- **Runtime strategy**: planner must account for both the bundled Ren’Py 8.4 SDK (`app/renpy-source-api/...`) and per-game bundled runtimes. Goal: ability to launch analysis inside the game’s native Python/Ren’Py environment for higher fidelity. Since Py2 and Py3 workers diverge, requirements include selecting the right worker per slot, packaging both workers, and documenting fallback order (bundled runtime first, then embedded SDK) as soon as feasible.

### 8. Open Questions Handed to the Planning Phase

1. Schema fidelity vs AHS: should cache tables mirror Authoritative Hierarchy structures or store raw SDK payloads and let consumers adapt?
2. Staleness detection: do we hash slot contents/check timestamps automatically, or rely on manual “re-run cache” actions?
3. Runtime guardrails: what execution time/memory thresholds are acceptable before we consider optimizations?
4. Inspector coverage: which mini-tools are mandatory for MVP versus deferred (label tracer, cache validator, BOM tester, AST dumper)?
5. Cache security/size constraints: any maximum cache size, sanitization requirements, or sharing policies?
6. Bundled runtime packaging: how do we distribute/select Py2 vs Py3 workers, and what is the definitive fallback order (bundled runtime vs embedded SDK)?
7. Logging artifact format: should per-slot logs be plain text, structured JSON, or leverage third-party logging helpers?

Document owner: FlowViz architecture track.
Last updated: _<fill during planning>_
