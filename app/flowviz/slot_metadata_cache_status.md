## Slot Metadata Cache – Status Log

> Last updated: 2025-12-01

This log captures the current state of the slot-cache plan as of December 1, 2025 (Windows 11 environment, PowerShell launcher). It ties each completed component back to the tasks in `slot_metadata_cache_plan.md`.

### Implemented

1. **CLI entry point (`run.py`)**

   - Added `flowviz-cache` subcommand that resolves slots, enforces source modes (rpyc-only, rpy-only, auto), selects runtimes, launches the SDK worker, captures raw payloads, and writes `cache/metadata.db`.
   - Added `flowviz-cache-inspect` and `flowviz-cache-validate` subcommands to support post-run diagnostics (`cache_reader.py`).

2. **Runtime selection & SDK worker integration**

   - Bundled runtime detection (via `runtime_locator.locate_bundled_python`) with Python-major probing; falls back to embedded Ren’Py 8.4 SDK if Py2-only runtime is found.
   - Environment setup for bundled SDKs (PATH, PYTHONHOME, FLOW\_\* variables) when Py3 runtimes are available.

3. **Cache writer & schema (`cache_writer.py`)**

   - Authoritative `metadata.db` per slot with tables: `cache_meta`, `labels`, `menus`, `menu_choices`, `edges`, `screens`.
   - Atomic temp-file swap, provenance metadata (story/slot IDs, runtime descriptor, analyzer version, source mode, payload counts).
   - Payload normalization from SDK worker output (labels/menus/outgoing flows/screens).

4. **Diagnostics tooling (`cache_reader.py`)**

   - `flowviz-cache-inspect` summary view plus per-label drilldown (menus, choices, outgoing edges).
   - `flowviz-cache-validate` ensures schema presence, cache_meta completeness, and basic relational integrity.

5. **Runtime logs & artifacts**
   - Each slot run writes `cache/flowviz_cache.log`, `sdk_worker_stdout.log`, `sdk_worker_stderr.log`, and `sdk_payload.json` alongside `metadata.db`.

### Pending / Open Questions (from plan)

1. **Schema fidelity vs. AHS alignment** – need to confirm whether additional tables (AHS node hashes, helper-label metadata) are required before downstream features consume the cache.
2. **Automatic cache staleness detection** – no hashing or mtime tracking yet. Re-runs overwrite caches manually.
3. **Performance guardrails** – no runtime/memory thresholds or progress reporting yet.
4. **Tooling roadmap** – inspector/validator exist, but BOM tester, AST chunk dumper, and standalone analyzer CLI ergonomics still need outlining.
5. **Cache size/security policy** – no limits or sanitization rules defined for sharing caches externally.
6. **Bundled runtime packaging for Py2** – detection exists but still falls back to embedded SDK; full Py2 worker parity remains future work.
7. **Log format** – current logs are plain text; decision pending on structured/JSON logs per plan.

### Next Suggested Steps

1. Expand inspector tooling to include screen/action views and graph-oriented exports for FlowViz UI consumption.
2. Decide on schema alignment with Authoritative Hierarchy System before wiring Dialog Search / Decision Points to the cache.
3. Design staleness detection (hash-based or timestamp-based) so the validator can warn users when slot sources changed after last extraction.

Please update this log whenever key plan milestones are reached or open questions are resolved.
